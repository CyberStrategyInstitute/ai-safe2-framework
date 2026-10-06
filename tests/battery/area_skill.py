"""SKILL area: skills/ structural integrity and the skill trust gate."""
import re
import sys
from pathlib import Path

AREA = "SKILL"


def run(ctx):
    rc, out = ctx.run([ctx.py, "-I", ctx.fx / "check_skill_area.py", ctx.repo])
    m = re.search(r"PASS (\d+)\s+WARN (\d+)\s+FAIL (\d+)", out)
    fails = int(m.group(3)) if m else -1
    ctx.rec(AREA, "structure+referential integrity", fails == 0, m.group(0) if m else out[-200:], "0 FAIL")
    for line in out.splitlines():
        if line.startswith("FAIL "):
            ctx.rec(AREA, "  struct: " + line[5:60], False, line[5:])

    lab = ctx.work / "skills"
    lab.mkdir()
    ctx.run([sys.executable, "-I", ctx.fx / "make_skills.py", lab])
    approved = []
    for d in sorted(lab.iterdir()):
        rc, _ = ctx.run([ctx.safe2, "gate", "skill", d, "--strict"], timeout=120)
        verdict = {0: "APPROVE", 1: "REJECT", 2: "HOLD"}.get(rc, f"exit{rc}")
        if d.name.startswith("B"):
            # B3 quotes an attack phrase: HOLD by default, REJECT is correct under --strict.
            ok = rc == 0 or (d.name.startswith("B3") and rc in (1, 2))
            ctx.rec(AREA, f"gate benign {d.name}", ok, verdict, "APPROVE (B3: HOLD/REJECT)")
        else:
            if rc == 0:
                approved.append(d.name)
            ctx.rec(AREA, f"gate hostile {d.name}", rc in (1, 2), verdict, "not APPROVE")
    hostile = len([d for d in lab.iterdir() if d.name.startswith("H")])
    ctx.rec(AREA, "hostile skills approved (total)", not approved, f"{len(approved)}/{hostile} {approved}", "0")

    rc, out = ctx.run([ctx.safe2, "gate", "skill", ctx.repo / "skills"], timeout=120)
    ctx.rec(AREA, "INFO skills/ root package boundary", True,
            f"exit={rc}; package includes MCP test corpus={'skills/mcp/tests/' in out}",
            "packaging finding, not a gate defect", status="INFO")
    rejected = []
    for d in sorted((Path(ctx.repo) / "skills/codex").glob("*/")):
        if (d / "SKILL.md").exists():
            rc, _ = ctx.run([ctx.safe2, "gate", "skill", d], timeout=120)
            if rc == 1:
                rejected.append(d.name)
    ctx.rec(AREA, "repo's codex skills not rejected", not rejected, f"rejected={rejected}", "none")
