"""Installed-package acceptance run for the Challenge 001 controlled seam."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if (REPOSITORY_ROOT / "ai-safe2.manifest.json").is_file():
    sys.path.insert(0, str(REPOSITORY_ROOT))


def main() -> None:
    from safe2.challenge.execution import create_plan, execute_plan, verify_execution

    executor = Path(__file__).with_name("executor.py")
    plan = create_plan(
        [sys.executable, str(executor)], provider_name="AI SAFE2 controlled example",
        provider_version="1.0", producer_id="ai-safe2-example",
        treatment="controlled-reference",
    )
    source, run, receipt = execute_plan(plan)
    verification = verify_execution(plan, source, run, receipt)
    print(json.dumps({
        "valid": verification["valid"], "episodes": run["summary"]["episodes"],
        "incomplete": run["summary"]["status_counts"]["incomplete"],
        "process_sandboxed": receipt["claims"]["process_sandboxed"],
        "independent_replication": receipt["claims"]["independent_replication"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
