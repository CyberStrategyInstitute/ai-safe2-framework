"""Installed-wheel smoke test; run with -I to exclude checkout imports."""

import json
import subprocess
import sys
import tempfile
from importlib.resources import files
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="safe2-receipt-wheel-") as temporary:
        root = Path(temporary)
        data = files("safe2").joinpath("data")
        for name in ("task-receipt-demo.json", "task-receipt-demo.txt"):
            (root / name).write_bytes(data.joinpath(name).read_bytes())

        def invoke(*arguments):
            completed = subprocess.run([sys.executable, "-I", "-m", "safe2", *arguments],
                                       cwd=root, capture_output=True, timeout=90, check=True)
            return json.loads(completed.stdout)

        receipt = invoke("feedback", "receipt", str(root / "task-receipt-demo.json"),
                         "--artifact-root", str(root))
        assert receipt["completion_verified"] is False
        for contract in ("task-receipt-input-v1", "task-receipt-v1", "test-result-v1",
                         "tool-result-v1", "report-attestation-v1", "usage-summary-v1", "pytest-capture-v1"):
            invoke("schema", "export", contract)
        (root / "test_demo.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        capture = root / "capture.json"
        invoke("feedback", "capture-pytest", "--execute", "--python", str(Path(sys.executable).resolve(strict=True)),
               "--cwd", str(root), "--task-id", "wheel-demo", "--revision", "synthetic",
               "--environment", "local", "--call-id", "pytest-1", "--output", str(capture), "test_demo.py")
        checked = invoke("feedback", "verify-pytest", str(capture))
        assert checked["internally_consistent"] is True
        assert checked["all_tests_passed_claim"]["status"] == "supported"
        assert checked["execution_verified"] is False
    print("Installed distribution: receipts, seven schemas, pytest capture and verification passed")


if __name__ == "__main__":
    main()
