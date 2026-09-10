"""Optional NVIDIA SkillSpector CLI adapter using its public JSON contract."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from safe2.bounded_files import inventory
from safe2.bounded_process import run_bounded
from safe2.challenge.io import parse_json, read_bytes, safe_path


def _target_digest(
    target: Path, *, max_files: int = 10_000, max_bytes: int = 100_000_000
) -> str:
    digest = hashlib.sha256(b"safe2-target-v2\\0")
    try:
        target = safe_path(target)
        paths = inventory(target, max_entries=max_files)
        total = 0
        for path in paths:
            name = path.relative_to(target.parent).as_posix().encode("utf-8")
            data = read_bytes(path, limit=max_bytes - total)
            total += len(data)
            # Length framing prevents path/content boundary ambiguity.
            digest.update(len(name).to_bytes(8, "big"))
            digest.update(name)
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(hashlib.sha256(data).digest())
    except (OSError, ValueError) as exc:
        raise RuntimeError("SkillSpector target is unsafe or exceeds inventory/byte limits") from exc
    return digest.hexdigest()

def collect(
    target: str,
    *,
    no_llm: bool = True,
    executable: str = "skillspector",
    timeout: float = 300.0,
    max_output_bytes: int = 10_000_000,
) -> dict:
    binary = shutil.which(executable)
    if not binary:
        raise RuntimeError(
            "SkillSpector is not installed or not on PATH. Install it separately; "
            "use Python 3.12-3.14 for SkillSpector 2.11.1 and pass --executable. "
            "No assessment was performed."
        )
    try:
        target_path = safe_path(target)
    except (OSError, ValueError) as exc:
        raise RuntimeError("SkillSpector target path is unsafe") from exc
    if not target_path.exists():
        raise RuntimeError(f"SkillSpector target does not exist: {target}")
    digest_before = _target_digest(target_path)
    command = [binary, "scan", str(target_path), "--format", "json"]
    if no_llm:
        command.append("--no-llm")
    try:
        version_result = run_bounded([binary, "--version"], timeout=10, max_bytes=4096)
        provider_version = (
            (version_result.stdout or version_result.stderr).decode("utf-8", errors="replace").strip()[:200] or "unknown"
        )
        if version_result.returncode != 0 or version_result.exceeded:
            provider_version = "unknown"
        completed = run_bounded(command, timeout=timeout, max_bytes=max_output_bytes)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"SkillSpector exceeded the {timeout:g}-second timeout") from exc
    if completed.returncode not in (0, 1):
        raise RuntimeError("SkillSpector assessment failed with an unsupported exit code")
    if completed.exceeded:
        raise RuntimeError("SkillSpector output exceeds the byte limit")
    try:
        source = parse_json(completed.stdout)
    except ValueError as exc:
        if str(exc) == "Artifact must be a JSON object":
            raise TypeError("SkillSpector JSON output must be an object") from exc
        raise RuntimeError("SkillSpector did not return valid JSON") from exc
    if not isinstance(source, dict):
        raise TypeError("SkillSpector JSON output must be an object")
    digest_after = _target_digest(target_path)
    if digest_before != digest_after:
        raise RuntimeError("SkillSpector target changed during assessment")
    return {
        "schema_version": "safe2.skillspector-evidence.v1",
        "provider": {
            "name": "NVIDIA SkillSpector",
            "mode": "static" if no_llm else "static-and-semantic",
            "version": provider_version,
            "upstream": "https://github.com/NVIDIA/SkillSpector",
            "license": "Apache-2.0",
        },
        "collected_at": datetime.now(UTC).isoformat(),
        "target": {"path": str(target_path), "sha256": digest_after},
        "source_contract": source.get("schema_version", "unversioned-json"),
        "source_result": source,
        "source_exit_code": completed.returncode,
        "attribution": "Independent evidence provider; no NVIDIA endorsement or certification is implied.",
        "conformance_claim": False,
        "limitations": [
            "Adapter compatibility is bounded to the recorded provider version and JSON output contract.",
            "Scanner findings are evidence inputs, not AI SAFE2 conformance decisions.",
        ],
    }
