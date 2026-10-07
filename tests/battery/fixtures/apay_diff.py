"""Differential test: main's nexus-apay.rego (OPA 0.65) vs rewritten policy (OPA 1.x).
usage: apay_diff.py OLD_POLICY NEW_POLICY TEST_MODULE_PATH OPA_BIN OPA_LEGACY_BIN
OLD_POLICY is evaluated on OPA_LEGACY_BIN (0.65), NEW_POLICY on OPA_BIN (1.x).
Any input where the new policy is LOOSER (allows/releases where old denied) is a failure.
Stricter differences are listed for review."""
import copy, importlib.util, json, random, subprocess, sys, tempfile
OLD, NEW, TESTMOD, OPA1, OPA065 = sys.argv[1:6]

spec = importlib.util.spec_from_file_location("apay_t", TESTMOD)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
fx = m.sample_input
fn = getattr(fx, "__wrapped__", None) or getattr(fx, "_get_wrapped_function", lambda: None)() or getattr(fx, "_fixture_function", None)
base = json.loads(json.dumps(fn(), default=str))

def leaves(o, p=()):
    if isinstance(o, dict):
        for k, v in o.items(): yield from leaves(v, p + (k,))
    elif isinstance(o, list) and o and not all(isinstance(x, (str, int, float)) for x in o):
        for i, v in enumerate(o): yield from leaves(v, p + (i,))
    else:
        yield p, o

def setp(o, p, v, delete=False):
    o = copy.deepcopy(o); cur = o
    for k in p[:-1]: cur = cur[k]
    if delete:
        if isinstance(cur, dict): cur.pop(p[-1], None)
        else: cur[p[-1]] = None
    else: cur[p[-1]] = v
    return o

def mutations(v):
    out = [("del", None), ("null", None)]
    if isinstance(v, bool): out.append(("flip", not v))
    elif isinstance(v, (int, float)): out += [("zero", 0), ("neg", -abs(v) - 1), ("big", v * 1000 + 10**9)]
    elif isinstance(v, str): out += [("empty", ""), ("other", v + "-x"), ("upper", v.upper())]
    elif isinstance(v, list): out += [("emptylist", []), ("extra", v + ["zz-extra"])]
    return out

cases = [("base", base)]
for p, v in leaves(base):
    for name, nv in mutations(v):
        cases.append((f"{'.'.join(map(str, p))}:{name}", setp(base, p, nv, delete=(name == "del"))))
random.seed(7)
singles = cases[1:]
for _ in range(400):
    (a, ia), (b, ib) = random.sample(singles, 2)
    merged = copy.deepcopy(ia)
    for p, v in leaves(ib):
        try:
            if v != dict(leaves(base)).get(p, object()): merged = setp(merged, p, v)
        except Exception: pass
    cases.append((f"{a} + {b}", merged))

def batch(opa, pol, inputs):
    # one OPA process per policy: evaluate every input via data.cases
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump({"cases": [c for _, c in inputs]}, fh); d = fh.name
    with tempfile.NamedTemporaryFile("w", suffix=".rego", delete=False) as fh:
        q = fh.name
    hdr = "package harness\nimport rego.v1\n" if opa == OPA1 else "package harness\n"
    open(q, "w").write(hdr + "results = [r | c := data.cases[_]; "
                       "dd := data.nexus.apay.decision with input as c; "
                       "rl := data.nexus.apay.release_credential with input as c; r := {\"d\": dd, \"rel\": rl}]\n")
    r = subprocess.run([opa, "eval", "-f", "json", "-d", pol, "-d", q, "-d", d, "data.harness.results"], capture_output=True, text=True)
    out = json.loads(r.stdout or "{}")
    if "result" not in out: sys.exit(f"eval failed on {pol}: {(r.stderr or r.stdout)[:700]}")
    return out["result"][0]["expressions"][0]["value"]

old = batch(OPA065, OLD, cases); new = batch(OPA1, NEW, cases)
looser, stricter, same = [], [], 0
for (cid, _), o, n in zip(cases, old, new):
    ko = (o["d"].get("decision"), tuple(sorted(o["d"].get("reason_codes", []))), o["rel"])
    kn = (n["d"].get("decision"), tuple(sorted(n["d"].get("reason_codes", []))), n["rel"])
    if ko == kn: same += 1; continue
    allow_o, allow_n = o["d"].get("decision") == "allow", n["d"].get("decision") == "allow"
    if (allow_n and not allow_o) or (n["rel"] and not o["rel"]): looser.append((cid, ko, kn))
    else: stricter.append((cid, ko, kn))
base_dec = new[0]["d"].get("decision")
print(f"inputs={len(cases)} identical={same} stricter={len(stricter)} looser={len(looser)} base_decision_new={base_dec} base_decision_old={old[0]['d'].get('decision')}")
for x in looser[:10]: print("LOOSER", x)
for x in stricter[:12]: print("STRICTER", x)
print("PASS" if not looser else "FAIL", "apay rewrite never loosens a decision")
