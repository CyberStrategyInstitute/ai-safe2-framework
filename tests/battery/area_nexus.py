"""NEXUS area: Guardian evasion, AgBOM integrity, SDK tests, OPA policies, scoring."""
import re
from pathlib import Path

AREA = "NEXUS"


def _parse(ctx, out, prefix, pattern):
    for line in out.splitlines():
        m = re.match(pattern, line)
        if m:
            yield m


def run(ctx):
    rc, out = ctx.run([ctx.py, "-I", ctx.fx / "guardian_cases.py"], timeout=120)
    (ctx.out_dir / "guardian_raw.txt").write_text(out)
    for m in _parse(ctx, out, "", r"(PASS|FAIL)\s+(.+?)\s+want=(\S+)\s+got=(\S+)"):
        ctx.rec(AREA, "guardian: " + m.group(2).strip(), m.group(1) == "PASS", f"got {m.group(4)}", m.group(3))

    rc, out = ctx.run([ctx.py, "-I", ctx.fx / "agbom_checks.py"], timeout=60)
    for m in _parse(ctx, out, "", r"(PASS|FAIL)\s+(.+?)\s+::\s+(.*)"):
        ctx.rec(AREA, "agbom: " + m.group(2), m.group(1) == "PASS", m.group(3))

    rc, out = ctx.run([ctx.py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "sdk/python/tests"],
                      timeout=600, cwd=ctx.repo / "NEXUS")
    passed, failed = re.search(r"(\d+) passed", out), re.search(r"(\d+) failed", out)
    ctx.rec(AREA, "SDK test suite", rc == 0,
            (passed.group(0) if passed else "") + (" " + failed.group(0) if failed else ""), "all pass")

    if not ctx.opa:
        ctx.not_run(AREA, "OPA policy checks", "no OPA 1.x binary (set OPA_BIN)")
    else:
        rc, out = ctx.run([ctx.opa, "check", "--strict", ctx.repo / "NEXUS/opa"], timeout=60)
        ctx.rec(AREA, "OPA 1.x: policies compile (--strict)", rc == 0,
                out.strip().splitlines()[0][:150] if out.strip() else "ok", "compiles")
        rc, out = ctx.run([ctx.opa, "test", ctx.repo / "NEXUS/opa", "-v"], timeout=120)
        p, f = len(re.findall(r": PASS", out)), len(re.findall(r": (FAIL|ERROR)", out))
        ctx.rec(AREA, "OPA 1.x: opa test", rc == 0 and p > 0, f"{p} pass {f} fail rc={rc}", "all pass")
        legacy = [ctx.opa_legacy] if ctx.opa_legacy else []
        rc, out = ctx.run([ctx.py, "-I", ctx.fx / "opa_contract.py", ctx.repo, ctx.opa, *legacy], timeout=120)
        for m in _parse(ctx, out, "", r"(PASS|FAIL)\s+(.+?)\s+::\s+(.*)"):
            ctx.rec(AREA, "opa: " + m.group(2), m.group(1) == "PASS", m.group(3))
        if "evaluates on OPA 1.x :: no" in out and not ctx.opa_legacy:
            ctx.not_run(AREA, "opa: authz semantic contract", "policy does not load on 1.x and no legacy binary given")
    if ctx.opa_legacy:
        rc, out = ctx.run([ctx.opa_legacy, "check", "--strict", ctx.repo / "NEXUS/opa"], timeout=60)
        ctx.rec(AREA, "OPA 0.65 (compose pin): policies compile", rc == 0,
                out.strip().splitlines()[0][:150] if out.strip() else "ok", "compiles")
    else:
        ctx.not_run(AREA, "OPA 0.65 (compose pin): policies compile", "no legacy binary (set OPA_LEGACY_BIN)")

    wf = Path(ctx.repo) / ".github/workflows/opa.yml"
    txt = wf.read_text() if wf.exists() else ""
    ctx.rec(AREA, "CI runs OPA on NEXUS/opa", "NEXUS/opa" in txt,
            "path filter present" if "NEXUS/opa" in txt else "watches non-existent opa/**", "NEXUS/opa")
    compose = Path(ctx.repo) / "NEXUS/docker/docker-compose.yml"
    mounts = re.findall(r"^\s*-\s*(\S+):/policies", compose.read_text(), re.M) if compose.exists() else []
    ok = bool(mounts) and all((compose.parent / m).resolve().joinpath("nexus-authz.rego").exists() for m in mounts)
    ctx.rec(AREA, "compose OPA mount resolves to the policies", ok, f"mounts={mounts}", "points at NEXUS/opa")
    _scorer_agrees_with_evidence(ctx)


def _scorer_agrees_with_evidence(ctx):
    """nexus-score must not report OK for a control this battery just showed broken."""
    mine = {r["id"]: r["status"] for r in ctx.results if r["area"] == AREA}
    broken = {
        "S1.3-GIP": any(k.startswith("guardian:") and v == "FAIL" for k, v in mine.items()),
        "A2.3-AGBOM": any(k.startswith("agbom:") and v == "FAIL" for k, v in mine.items()),
        "AISM-OPA": mine.get("OPA 1.x: policies compile (--strict)") == "FAIL"
                    or mine.get("OPA 0.65 (compose pin): policies compile") == "FAIL",
    }
    env = {**ctx.env, **({"OPA_BIN": ctx.opa} if ctx.opa else {})}
    rc, out = ctx.run([ctx.py, ctx.repo / "NEXUS/compliance/scoring/nexus-score.py", "--v03-checks"], timeout=120, env=env)
    (ctx.out_dir / "nexus_score_raw.txt").write_text(out)
    claims = {cid: ("OK" if f"[OK ] {cid} " in out else "not OK") for cid in broken}
    contradictions = [cid for cid, is_broken in broken.items() if is_broken and claims[cid] == "OK"]
    ctx.rec(AREA, "nexus-score claims agree with battery evidence", not contradictions,
            f"claims OK for broken: {contradictions}" if contradictions else f"exit={rc} claims={claims}",
            "no OK on a broken control")
