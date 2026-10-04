"""Qualify an installed SAFE2 wheel outside its source tree using only public surfaces."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
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


def qualify(expected_version: str) -> None:
    installed = importlib.metadata.version("ai-safe2")
    if installed != expected_version:
        raise RuntimeError(f"installed version {installed!r} != expected {expected_version!r}")
    entry = Path(sysconfig.get_path("scripts")) / ("safe2.exe" if os.name == "nt" else "safe2")
    if not entry.is_file():
        raise RuntimeError("safe2 console entry point is absent from the active environment")
    version = run("--version").stdout.strip()
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


def check_tag(tag: str, expected_version: str) -> None:
    normalized = tag.removeprefix("v")
    if normalized != expected_version:
        raise RuntimeError(
            f"release tag {tag!r} does not match package version {expected_version!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", default="1.0.0")
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
