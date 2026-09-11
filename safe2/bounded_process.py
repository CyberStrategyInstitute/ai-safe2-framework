"""Run subprocesses without permitting unbounded in-memory output."""

from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BoundedResult:
    returncode: int
    stdout: bytes
    stderr: bytes
    exceeded: bool = False
    output_complete: bool = True


def run_bounded(
    command: list[str], *, timeout: float, max_bytes: int, stdin: bytes | None = None,
    cwd: Path | None = None, env: dict[str, str] | None = None,
) -> BoundedResult:
    """Capture at most max_bytes across stdout/stderr and terminate on overflow."""
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=env,
    )
    output = {"stdout": bytearray(), "stderr": bytearray()}
    exceeded = threading.Event()
    drain_failed = threading.Event()
    lock = threading.Lock()

    def drain(name: str) -> None:
        stream = getattr(process, name)
        assert stream is not None
        try:
            while chunk := stream.read(65_536):
                with lock:
                    remaining = max_bytes - len(output["stdout"]) - len(output["stderr"])
                    if remaining <= 0:
                        exceeded.set()
                        process.kill()
                        return
                    output[name].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        exceeded.set()
                        process.kill()
                        return
        except (OSError, ValueError):
            drain_failed.set()

    threads = [threading.Thread(target=drain, args=(name,), daemon=True) for name in output]
    for thread in threads:
        thread.start()
    try:
        if stdin is not None and process.stdin is not None:
            process.stdin.write(stdin)
            process.stdin.close()
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise
    finally:
        for thread in threads:
            thread.join(timeout=1)
    with lock:
        complete = (not any(thread.is_alive() for thread in threads)
                    and not exceeded.is_set() and not drain_failed.is_set())
        return BoundedResult(process.returncode, bytes(output["stdout"]), bytes(output["stderr"]),
                             exceeded.is_set(), complete)
