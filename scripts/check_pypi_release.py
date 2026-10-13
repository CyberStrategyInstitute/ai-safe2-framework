#!/usr/bin/env python3
"""Confirm that published CLI releases actually reached PyPI.

Why: CLI 1.0.0 was released on GitHub on 2026-10-05 but never reached PyPI,
because the publish workflow skipped the tag. Nothing reported it, and the
README's install command failed for anyone who followed it.

  wait   After an upload, poll PyPI until VERSION is listed (or time out).
  audit  Given GitHub releases JSON (`gh api repos/O/R/releases`), fail when the
         newest published, non-prerelease CLI release is not on PyPI. Older CLI
         releases that are missing are reported but do not fail: several 0.x
         releases predate PyPI publishing.

Exit codes: 0 ok, 1 missing from PyPI, 2 usage or network error.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_release_installation import cli_version_from_tag  # noqa: E402

PACKAGE = "ai-safe2"


def pypi_versions(package: str = PACKAGE, timeout: float = 20.0) -> set[str]:
    url = f"https://pypi.org/pypi/{package}/json"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https URL
        data = json.load(response)
    return {v for v, files in data.get("releases", {}).items() if files}


def wait_for(version: str, fetch: Callable[[], set[str]], timeout_s: float, interval_s: float,
             sleep: Callable[[float], None] = time.sleep) -> bool:
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            if version in fetch():
                return True
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"PyPI not reachable yet: {exc}", file=sys.stderr)
        if time.monotonic() >= deadline:
            return False
        sleep(interval_s)


def audit(releases: list[dict], published: set[str]) -> tuple[list[str], list[str]]:
    """Return (failures, warnings) for CLI releases missing from PyPI."""
    cli = []
    for rel in releases:
        if rel.get("draft") or rel.get("prerelease"):
            continue
        version = cli_version_from_tag(str(rel.get("tag_name", "")))
        if version:
            cli.append((str(rel.get("published_at") or ""), rel["tag_name"], version))
    if not cli:
        return [], ["no published CLI releases found"]
    cli.sort(reverse=True)
    failures, warnings = [], []
    newest_at, newest_tag, newest_version = cli[0]
    if newest_version not in published:
        failures.append(
            f"newest CLI release {newest_tag} ({newest_at}) is version {newest_version}, "
            f"which PyPI does not serve; `pip install {PACKAGE}=={newest_version}` fails"
        )
    for _, tag, version in cli[1:]:
        if version not in published:
            warnings.append(f"older CLI release {tag} ({version}) is not on PyPI")
    return failures, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("wait")
    w.add_argument("--version", required=True)
    w.add_argument("--package", default=PACKAGE)
    w.add_argument("--timeout", type=float, default=600)
    w.add_argument("--interval", type=float, default=20)
    a = sub.add_parser("audit")
    a.add_argument("--releases-json", type=Path, required=True)
    args = ap.parse_args(argv)

    if args.cmd == "wait":
        fetch = lambda: pypi_versions(args.package)  # noqa: E731
        if wait_for(args.version, fetch, args.timeout, args.interval):
            print(f"PyPI serves {args.package} {args.version}")
            return 0
        print(f"::error::PyPI does not list {args.package} {args.version} after {args.timeout:.0f}s")
        return 1

    try:
        releases = json.loads(args.releases_json.read_text(encoding="utf-8"))
        if isinstance(releases, dict):
            releases = [releases]
        published = pypi_versions()
    except (OSError, json.JSONDecodeError, urllib.error.URLError, TimeoutError) as exc:
        print(f"::error::release audit could not run: {exc}")
        return 2
    failures, warnings = audit(releases, published)
    for line in warnings:
        print(f"::warning::{line}")
    for line in failures:
        print(f"::error::{line}")
    if not failures:
        print(f"newest CLI release is on PyPI ({PACKAGE} versions: {', '.join(sorted(published))})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
