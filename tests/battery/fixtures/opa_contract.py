"""NEXUS authz OPA contract probe. usage: opa_contract.py REPO OPA_BIN [OPA_LEGACY_BIN]
Evaluates with OPA 1.x; if the policy does not compile there and a legacy binary
(0.65, the compose pin) is given, falls back to it so semantic defects are measured
separately from the syntax defect."""
import json, subprocess, sys, tempfile, os
REPO, OPA = sys.argv[1], sys.argv[2]
OPA065 = sys.argv[3] if len(sys.argv) > 3 else None
POL = f"{REPO}/NEXUS/opa/nexus-authz.rego"
DATA = {"nexus": {"mandates": {"active": {"M-1": True}},
                  "revocation": {"agents": {"did:r": {"status": "revoked"}}},
                  "approvals": {"config_change": {"did:a": {"h1": True}}}}}
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
    fh.write(json.dumps(DATA)); dpath = fh.name

def ev(binary, inp):
    r = subprocess.run([binary, "eval", "-f", "json", "-d", POL, "-d", dpath, "-I",
                        "data.nexus.authz.authorize_tool_call"], input=json.dumps(inp), capture_output=True, text=True)
    try:
        doc = json.loads(r.stdout)
        if "result" not in doc or not doc["result"]:
            return {"_undefined": True} if r.returncode == 0 else {"_error": (r.stderr or r.stdout)[:160]}
        return doc["result"][0]["expressions"][0]["value"]
    except Exception:
        return {"_error": (r.stderr or r.stdout)[:160]}

base = {"agent_id": "did:a", "tool_name": "read_doc", "vcc_capabilities": ["read_doc", "credential:vault", "update_config", "mem"],
        "vcc_mandate_required": [], "delegation_depth": 1, "context_compartment": "TASK_CONTEXT",
        "parent_vcc_capabilities": ["read_doc"], "requested_new_capabilities": [], "act_tier": 1}
def C(**kw): d = dict(base); d.update(kw); return d

probe = ev(OPA, base)
binary = OPA if "_error" not in probe else OPA065
print(f"{'PASS' if binary == OPA else 'FAIL'} evaluates on OPA 1.x :: {'yes' if binary == OPA else 'no: ' + probe['_error'][:90]}")
if binary is None:
    sys.exit(0)  # no legacy binary: semantic cases are NOT_RUN, recorded by the caller as absent

cases = [
 ("baseline capability allowed", True, C()),
 ("durable memory write w/o mandate denied", False, C(tool_name="mem", performative="memory_write", memory_zone="PERMANENT")),
 ("durable memory write with mandate allowed", True, C(tool_name="mem", performative="memory_write", memory_zone="PERMANENT", mandate_id="M-1")),
 ("scope downgrade: PERMANENT zone + 'request' scope denied", False, C(tool_name="mem", performative="memory_write", memory_zone="PERMANENT", persistence_scope="request")),
 ("unrecognized scope 'Durable ' w/o mandate denied", False, C(tool_name="mem", performative="memory_write", persistence_scope="Durable ")),
 ("credential: tool from TASK_CONTEXT denied", False, C(tool_name="credential:vault")),
 ("config_change ACT-2 w/o approval denied", False, C(tool_name="update_config", performative="config_change", act_tier=2, change_hash="zz")),
 ("config_change ACT-2 with approval allowed", True, C(tool_name="update_config", performative="config_change", act_tier=2, change_hash="h1")),
 ("revoked agent denied", False, C(agent_id="did:r")),
 ("scope widening denied", False, C(requested_new_capabilities=["payments:wire"])),
 ("delegation depth 5 denied", False, C(delegation_depth=5)),
 ("missing delegation depth denied", False, {k: v for k, v in base.items() if k != "delegation_depth"}),
 ("unknown compartment denied", False, C(context_compartment="WHATEVER")),
]
for cid, want, inp in cases:
    d = ev(binary, inp)
    got = d.get("allow") if isinstance(d, dict) else None
    ok = (got is True) if want else (got is not True)
    extra = f" deny_reason='{d.get('deny_reason','')}'" if not want else ""
    print(f"{'PASS' if ok else 'FAIL'} {cid} :: allow={got}{extra}{' ERR ' + d['_error'][:80] if '_error' in d else ''}{' (decision UNDEFINED)' if d.get('_undefined') else ''}")
undef = [cid for cid, _w, inp in cases if ev(binary, inp).get("_undefined")]
print(f"{'PASS' if not undef else 'FAIL'} decision defined for every input :: undefined for {len(undef)}/{len(cases)}")
d = ev(binary, C(tool_name="credential:vault"))
print(f"{'PASS' if d.get('deny_reason') else 'FAIL'} deny_reason explains a denial :: '{d.get('deny_reason','')}'")
os.unlink(dpath)
