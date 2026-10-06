"""CLI area: end-to-end safe2 command behavior, exit codes, and tamper handling."""
import re

AREA = "CLI"


def run(ctx):
    rc, out = ctx.run(["bash", ctx.fx / "cli_battery.sh", ctx.venv, ctx.repo, ctx.work / "cli"], timeout=900)
    (ctx.out_dir / "cli_raw.txt").write_text(out)
    seen = 0
    for line in out.splitlines():
        m = re.match(r"(\S+)\s+exit=(\S+)\s+want=(\S+)\s+(PASS|FAIL)\s*(.*)", line)
        if m:
            seen += 1
            ctx.rec(AREA, m.group(1), m.group(4) == "PASS", f"exit={m.group(2)} {m.group(5)[:80]}", f"exit {m.group(3)}")
    if not seen:
        ctx.rec(AREA, "CLI battery produced results", False, out[-300:], "case lines")
