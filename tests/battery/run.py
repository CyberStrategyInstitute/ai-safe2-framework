#!/usr/bin/env python3
"""False-assurance battery runner. See docs/assessments/2026-10-06-false-assurance/RUNBOOK.md.

  python tests/battery/run.py --label after --venv .venv --out-dir snapshots/after-<sha>
  python tests/battery/run.py --label after --venv .venv --out-dir DIR --areas nexus      # one area
  python tests/battery/run.py ... --resume      # skip areas already recorded for this revision

Each area writes <out-dir>/<area>.json as soon as it finishes, so an interrupted
run keeps every completed area. summary.json and MATRIX.md are rebuilt from
whatever area files exist.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import area_cli  # noqa: E402
import area_mcp  # noqa: E402
import area_nexus  # noqa: E402
import area_skill  # noqa: E402
from core import Ctx, git_rev  # noqa: E402

AREAS = {"skill": area_skill, "mcp": area_mcp, "cli": area_cli, "nexus": area_nexus}


def summarize(out_dir: Path) -> dict:
    areas, rows = {}, []
    for name in AREAS:
        f = out_dir / f"{name}.json"
        if not f.exists():
            areas[name.upper()] = {"status": "NOT_RUN"}
            continue
        doc = json.loads(f.read_text())
        counts = {}
        for r in doc["results"]:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            rows.append(r)
        areas[name.upper()] = {"revision": doc["revision"], "counts": counts, "duration_s": doc["duration_s"]}
    summary = {"schema": "csi.battery.summary.v1", "areas": areas}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    lines = ["| Area | Revision | PASS | FAIL | NOT_RUN | INFO |", "|---|---|---|---|---|---|"]
    for a, v in areas.items():
        c = v.get("counts", {})
        lines.append(f"| {a} | {v.get('revision', '-')} | {c.get('PASS', 0)} | {c.get('FAIL', 0)} | "
                     f"{c.get('NOT_RUN', 0) + (1 if v.get('status') == 'NOT_RUN' else 0)} | {c.get('INFO', 0)} |")
    lines += ["", "## Failures and gaps", ""]
    lines += [f"- **{r['area']}** `{r['id'].strip()}`: {r['status']} - {r['detail'][:160]} (want: {r['want']})"
              for r in rows if r["status"] in ("FAIL", "NOT_RUN")] or ["- none"]
    (out_dir / "MATRIX.md").write_text("\n".join(lines) + "\n")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--venv", required=True, help="venv with safe2 + nexus-a2a-sdk installed from --repo")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--mcp-venv", help="venv with skills/mcp installed (defaults to --venv)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--areas", default=",".join(AREAS))
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--opa", default=os.environ.get("OPA_BIN") or shutil.which("opa"))
    ap.add_argument("--opa-legacy", default=os.environ.get("OPA_LEGACY_BIN"))
    a = ap.parse_args()

    repo, out_dir = Path(a.repo).resolve(), Path(a.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rev = git_rev(repo)
    ctx = Ctx(label=a.label, venv=Path(a.venv).resolve(), repo=repo,
              mcp_venv=Path(a.mcp_venv or a.venv).resolve(), out_dir=out_dir, opa=a.opa, opa_legacy=a.opa_legacy)
    try:
        for name in [x.strip().lower() for x in a.areas.split(",") if x.strip()]:
            f = out_dir / f"{name}.json"
            if a.resume and f.exists() and json.loads(f.read_text()).get("revision") == rev:
                print(f"[{a.label}] {name}: already recorded for {rev}, skipping", flush=True)
                continue
            started = time.time()
            try:
                AREAS[name].run(ctx)
            except Exception as e:
                ctx.rec(name.upper(), "AREA CRASHED", False, f"{type(e).__name__}: {e}")
            finally:
                ctx.cleanup()
                ctx.write_area(name.upper(), started)
    finally:
        ctx.close()
        s = summarize(out_dir)
        print("\nSUMMARY", a.label, rev, json.dumps({k: v.get("counts", v.get("status")) for k, v in s["areas"].items()}))


if __name__ == "__main__":
    main()
