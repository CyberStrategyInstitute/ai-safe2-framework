"""Project (161-control) scan engine.

Thin re-export of the existing scanner/ package (StaticScanner, ScanResult,
ISO42001Report) plus the tier-fail policy logic that used to live inline in
scanner/cli.py's `scan` command. Pulling it out here lets both
`safe2 scan project` and `safe2 gate project` share one policy
implementation instead of two copies drifting apart.
"""
from __future__ import annotations

from pathlib import Path

from scanner.report import ISO42001Report  # noqa: F401
from scanner.scanner import ScanResult, StaticScanner

DEFAULT_CONTROLS_JSON = Path(__file__).resolve().parent.parent / "data" / "ai-safe2-controls-v3.0.json"


def run_scan(
    path: str, controls_json: str | None = None, max_files: int = 10_000
) -> ScanResult:
    """Run the 161-control static audit against a project path.

    Falls back to the controls JSON bundled with the safe2 package if the
    caller didn't supply one and StaticScanner's own relative-path lookup
    (which assumes a repo checkout layout) doesn't find one either.
    """
    resolved = controls_json
    if resolved is None and DEFAULT_CONTROLS_JSON.exists():
        resolved = str(DEFAULT_CONTROLS_JSON)
    scanner = StaticScanner(controls_json=resolved, max_files=max_files)
    return scanner.scan_project(path)


def tier_fail(result: ScanResult, tier: str) -> bool:
    """Same tier policy scanner/cli.py used: Tier3 strict, Tier2 balanced, Tier1 baseline."""
    if tier == "Tier3" and result.score < 90:
        return True
    if tier == "Tier2" and result.score < 70:
        return True
    return bool(tier == "Tier1" and result.score < 50)


def fails(result: ScanResult, tier: str, fail_under: float | None) -> bool:
    if result.meta.get("scan_truncated"):
        return True
    if fail_under is not None:
        return result.score < fail_under
    return tier_fail(result, tier)
