"""Qualify an installed SAFE2 wheel outside its source tree using only public surfaces."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path


def run(*arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, "-I", "-m", "safe2", *arguments],
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
        cwd=tempfile.gettempdir(),
    )
    if result.returncode != expected:
        raise RuntimeError(
            f"safe2 {' '.join(arguments)} returned {result.returncode}, expected {expected}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def run_entry(
    entry: Path, *arguments: str, expected: int = 0
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [os.fspath(entry), *arguments],
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
        cwd=tempfile.gettempdir(),
    )
    if result.returncode != expected:
        raise RuntimeError(
            f"safe2 entry point {' '.join(arguments)} returned {result.returncode}, "
            f"expected {expected}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def qualify(expected_version: str) -> None:
    installed = importlib.metadata.version("ai-safe2")
    if installed != expected_version:
        raise RuntimeError(f"installed version {installed!r} != expected {expected_version!r}")
    entry = Path(sysconfig.get_path("scripts")) / ("safe2.exe" if os.name == "nt" else "safe2")
    if not entry.is_file():
        raise RuntimeError("safe2 console entry point is absent from the active environment")
    version = run_entry(entry, "--version").stdout.strip()
    if expected_version not in version:
        raise RuntimeError(f"unexpected version output: {version!r}")
    self_check = json.loads(run("self-check", "--format", "json", "--strict").stdout)
    if self_check["verdict"] != "pass" or self_check["distribution"]["version"] != expected_version:
        raise RuntimeError("installed self-check did not pass for the expected distribution")
    run("schema", "list")
    run("example", "list")
    for example in ("aism-decision-card", "aism-remediation", "environment-decision-card"):
        run("example", "verify", example)
    with tempfile.TemporaryDirectory(prefix="safe2-acceptance-") as temporary:
        # macOS exposes /var through /private/var. Give the acceptance scope
        # guard the canonical OS-created path so it does not confuse that
        # platform alias with an untrusted user-controlled symlink.
        bundle = Path(temporary).resolve() / "bundle"
        run("acceptance", "run", os.fspath(bundle), "--strict")
        run("acceptance", "verify", os.fspath(bundle))
    for command in ("assess", "doctor", "evidence", "challenge", "aism"):
        run(command, "--help")


def verify_uninstalled() -> None:
    try:
        importlib.metadata.version("ai-safe2")
    except importlib.metadata.PackageNotFoundError:
        pass
    else:
        raise RuntimeError("ai-safe2 distribution metadata remains after uninstall")
    entry = Path(sysconfig.get_path("scripts")) / ("safe2.exe" if os.name == "nt" else "safe2")
    if entry.exists():
        raise RuntimeError("safe2 console entry point remains in the active environment after uninstall")


# Accepted CLI release tags: `v1.0.1`, or the dated house style containing
# `CLI_1.0.1` (for example `2026-10-05_CLI_1.0.1` or `2026-10-05_CLI_1.0.1_Title`). The version in the tag must
# equal pyproject.toml; anything else fails before a build is published.
_VERSION = r"(\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?(?:\.post\d+)?)"
_V_TAG = re.compile(rf"^v{_VERSION}$")
_CLI_TAG = re.compile(rf"(?:^|[_\-\s])CLI[_\-\s]v?{_VERSION}(?=$|[_\-\s][A-Za-z])", re.IGNORECASE)


def cli_version_from_tag(tag: str) -> str | None:
    """Return the CLI version a release tag names, or None if it names none."""
    for pattern in (_V_TAG, _CLI_TAG):
        match = pattern.search(tag.strip())
        if match:
            return match.group(1)
    return None


def check_tag(tag: str, expected_version: str) -> None:
    version = cli_version_from_tag(tag)
    if version is None:
        raise RuntimeError(
            f"release tag {tag!r} does not name a CLI version; use v{expected_version} "
            f"or <date>_CLI_{expected_version}"
        )
    if version != expected_version:
        raise RuntimeError(
            f"release tag {tag!r} names {version!r} but pyproject.toml is {expected_version!r}"
        )
    print(f"release tag {tag!r} matches package version {expected_version}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", default="1.0.1")
    parser.add_argument("--verify-uninstalled", action="store_true")
    parser.add_argument("--check-tag")
    args = parser.parse_args()
    if args.verify_uninstalled:
        verify_uninstalled()
    elif args.check_tag:
        check_tag(args.check_tag, args.expected_version)
    else:
        qualify(args.expected_version)


if __name__ == "__main__":
    main()
