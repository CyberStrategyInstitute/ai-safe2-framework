"""Conservative cross-task accounting of declarations, not provider billing verification."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from safe2.evidence.task_receipt import validate_task_input


def correlate_usage(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Deduplicate identical task inputs and reject ambiguous ownership or lineage."""
    if not 1 <= len(documents) <= 32:
        raise ValueError("Provide 1..32 task inputs")
    tasks: dict[str, dict[str, Any]] = {}
    duplicates = 0
    for document in documents:
        validate_task_input(document)
        task_id = document["task_id"]
        if task_id in tasks:
            if document != tasks[task_id]:
                raise ValueError("Conflicting versions of a task; select one accounting snapshot")
            duplicates += 1
        tasks[task_id] = document
    missing_parents = set()
    for task_id in tasks:
        seen = set()
        current = task_id
        while current in tasks:
            if current in seen:
                raise ValueError("Task lineage cycle detected")
            seen.add(current)
            parent = tasks[current]["parent_task_id"]
            if parent is None:
                break
            if parent not in tasks:
                missing_parents.add(parent)
                break
            current = parent
    ownership: dict[str, str] = {}
    rows = []
    for task_id, task in sorted(tasks.items()):
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for item in task["usage"]:
            if item["event_id"] in ownership:
                raise ValueError("Usage event has multiple task owners; refusing double counting")
            ownership[item["event_id"]] = task_id
            groups.setdefault((item["metric"], item["basis"]), []).append(item)
        totals = []
        for (metric, basis), events in sorted(groups.items()):
            known = [Decimal(str(item["value"])) for item in events if item["value"] is not None]
            totals.append({"metric": metric, "basis": basis, "event_count": len(events),
                           "known_sum": str(sum(known, Decimal(0))) if known else None})
        rows.append({"task_id": task_id, "parent_task_id": task["parent_task_id"],
                     "harness": task["harness"], "totals": totals,
                     "usage_present": bool(task["usage"])})
    return {
        "schema_version": "safe2.usage-summary.v1", "tasks": rows,
        "duplicate_inputs_ignored": duplicates, "unique_usage_events": len(ownership),
        "missing_parent_ids": sorted(missing_parents),
        "accounting_scope": "per_task_declared_events_only", "billing_verified": False,
        "limitations": [
            "Reported values and estimates remain separate and unauthenticated; missing is not zero.",
            "Inputs must represent exclusive incremental events, not overlapping cumulative snapshots.",
            "Renamed duplicate events and semantic overlap cannot be detected from identifiers alone.",
            "Elapsed totals are summed durations, not wall-clock time across parallel work.",
            "No subscription allocation, savings estimate, verified outcome ratio, or family rollup is computed.",
        ],
    }
