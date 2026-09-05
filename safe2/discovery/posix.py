"""Explicit, read-only discovery for WSL distributions and SSH-accessible hosts."""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable
from typing import Any

from safe2.bounded_process import run_bounded

Runner = Callable[..., subprocess.CompletedProcess[bytes]]
SSH_TARGET = re.compile(r"^(?:[A-Za-z0-9._-]+@)?[A-Za-z0-9][A-Za-z0-9._-]*$")
DISTRO_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]*$")
KNOWN_HARNESSES = {"codex", "claude-code", "antigravity", "hermes", "openclaw", "grok"}
MAX_PROBE_BYTES = 1_000_000
MAX_PROBE_LINES = 1_000

PROBE_SCRIPT = r"""
printf 'safe2-probe-v1\n'
printf 'os\t'; uname -s 2>/dev/null || printf 'unknown\n'
printf 'release\t'; uname -r 2>/dev/null || printf 'unknown\n'
for item in codex:codex:.codex claude-code:claude:.claude antigravity:antigravity:.antigravity hermes:hermes:.hermes openclaw:openclaw:.openclaw grok:grok:.grok; do
  id=${item%%:*}; rest=${item#*:}; cmd=${rest%%:*}; cfg=${rest#*:}
  bin=$(command -v "$cmd" 2>/dev/null || true)
  if [ -n "$bin" ]; then printf 'harness\t%s\tcommand\t%s\n' "$id" "$bin"; fi
  if [ -e "$HOME/$cfg" ]; then printf 'harness\t%s\tconfiguration\t%s\n' "$id" "$HOME/$cfg"; fi
done
for cmd in sh bash zsh fish pwsh; do
  bin=$(command -v "$cmd" 2>/dev/null || true)
  if [ -n "$bin" ]; then printf 'shell\t%s\t%s\n' "$cmd" "$bin"; fi
done
""".strip()


def _run(
    command: list[str],
    timeout: float,
    runner: Runner,
    *,
    stdin: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    if runner is subprocess.run:
        result = run_bounded(command, timeout=timeout, max_bytes=MAX_PROBE_BYTES, stdin=stdin)
        if result.exceeded:
            return subprocess.CompletedProcess(command, 125, result.stdout, result.stderr)
        return subprocess.CompletedProcess(command, result.returncode, result.stdout, result.stderr)
    return runner(command, input=stdin, capture_output=True, check=False, timeout=timeout)


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").replace("\x00", "")


def _parse_probe(stdout: bytes) -> dict[str, Any]:
    if len(stdout) > MAX_PROBE_BYTES:
        return {"status": "failed", "error_type": "probe_output_limit", "harnesses": [], "shells": []}
    lines = _decode(stdout).splitlines()[:MAX_PROBE_LINES]
    if not lines or lines[0].strip() != "safe2-probe-v1":
        return {"status": "failed", "error_type": "invalid_probe_response", "harnesses": [], "shells": []}
    system = "unknown"
    release = "unknown"
    harness_map: dict[str, dict[str, Any]] = {}
    shells: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) == 2 and parts[0] == "os":
            system = parts[1][:100]
        elif len(parts) == 2 and parts[0] == "release":
            release = parts[1][:100]
        elif len(parts) == 4 and parts[0] == "harness" and parts[1] in KNOWN_HARNESSES:
            row = harness_map.setdefault(parts[1], {"id": parts[1], "indicators": []})
            if len(row["indicators"]) < 10 and parts[2] in {"command", "configuration"}:
                row["indicators"].append({"kind": parts[2], "path": parts[3][:500]})
        elif (
            len(parts) == 3
            and parts[0] == "shell"
            and len(shells) < 20
            and parts[1] in {"sh", "bash", "zsh", "fish", "pwsh"}
        ):
            shells.append({"id": parts[1], "path": parts[2][:500]})
    return {
        "status": "completed",
        "system": system,
        "release": release,
        "harnesses": list(harness_map.values()),
        "shells": shells,
    }


def probe_wsl(distro: str, *, timeout: float = 10.0, runner: Runner = subprocess.run) -> dict[str, Any]:
    """Inspect one explicitly named WSL distribution with a fixed metadata-only script."""
    if not DISTRO_NAME.fullmatch(distro) or distro.startswith("-"):
        raise ValueError("invalid WSL distribution name")
    executable = shutil.which("wsl.exe") or shutil.which("wsl")
    base = {"id": f"wsl:{distro}", "type": "wsl_distribution", "target": distro}
    if not executable:
        return {**base, "status": "not_available", "harnesses": [], "shells": []}
    try:
        completed = _run([executable, "--distribution", distro, "--", "sh", "-lc", PROBE_SCRIPT], timeout, runner)
    except subprocess.TimeoutExpired:
        return {**base, "status": "failed", "error_type": "timeout", "harnesses": [], "shells": []}
    except OSError as exc:
        return {**base, "status": "failed", "error_type": type(exc).__name__, "harnesses": [], "shells": []}
    if completed.returncode != 0:
        return {**base, "status": "failed", "return_code": completed.returncode, "harnesses": [], "shells": []}
    return {**base, **_parse_probe(completed.stdout)}


def probe_ssh(
    target: str,
    *,
    port: int = 22,
    timeout: float = 10.0,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Inspect one explicit SSH target; BatchMode prevents password or host-key prompts."""
    if not SSH_TARGET.fullmatch(target) or target.startswith("-"):
        raise ValueError("invalid SSH target; use [user@]hostname without spaces or shell syntax")
    if not 1 <= port <= 65535:
        raise ValueError("SSH port must be between 1 and 65535")
    executable = shutil.which("ssh")
    base = {"id": f"ssh:{target}:{port}", "type": "ssh_host", "target": target, "port": port}
    if not executable:
        return {**base, "status": "not_available", "harnesses": [], "shells": []}
    command = [
        executable,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", f"ConnectTimeout={max(1, int(timeout))}",
        "-p", str(port),
        "--", target,
        "sh", "-s",
    ]
    try:
        completed = _run(command, timeout + 1.0, runner, stdin=PROBE_SCRIPT.encode("utf-8"))
    except subprocess.TimeoutExpired:
        return {**base, "status": "failed", "error_type": "timeout", "harnesses": [], "shells": []}
    except OSError as exc:
        return {**base, "status": "failed", "error_type": type(exc).__name__, "harnesses": [], "shells": []}
    if completed.returncode != 0:
        return {**base, "status": "failed", "return_code": completed.returncode, "harnesses": [], "shells": []}
    return {**base, **_parse_probe(completed.stdout)}
