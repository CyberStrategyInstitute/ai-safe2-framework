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
        for name in ("task-receipt-demo.json", "task-receipt-demo.txt", "harness-source-demo.json",
                     "system-identity-source-demo.json", "failure-source-demo.json",
                     "assessment-scope-source-demo.json"):
            (root / name).write_bytes(data.joinpath(name).read_bytes())

        def invoke(*arguments):
            completed = subprocess.run([sys.executable, "-I", "-m", "safe2", *arguments],
                                       cwd=root, capture_output=True, timeout=90, check=True)
            return json.loads(completed.stdout)

        receipt = invoke("feedback", "receipt", str(root / "task-receipt-demo.json"),
                         "--artifact-root", str(root))
        assert receipt["completion_verified"] is False
        for contract in ("task-receipt-input-v1", "task-receipt-v1", "test-result-v1",
                         "tool-result-v1", "report-attestation-v1", "usage-summary-v1", "pytest-capture-v1",
                         "harness-source-v1", "harness-evidence-v1", "system-identity-source-v1",
                         "system-identity-manifest-v1", "failure-source-v1", "failure-diagnosis-v1",
                         "assessment-scope-source-v1", "assessment-scope-manifest-v1"):
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
        harness_output = root / "harness-evidence.json"
        harness = invoke("evidence", "harness", str(root / "harness-source-demo.json"),
                         "--output", str(harness_output))
        assert harness["completion_verified"] is False
        assert harness["conformance_claim"] is False
        assert harness["summary"]["coverage_missing"] == 3
        evidence = json.loads(harness_output.read_text(encoding="utf-8"))
        assert evidence["decision_scope"] == "evidence_inventory_only"
        assert evidence["source"]["authentication"] == "not_checked"
        identity_output = root / "system-identity.json"
        identity = invoke("evidence", "system", str(root / "system-identity-source-demo.json"),
                          "--output", str(identity_output), "--strict")
        assert identity["identity_verified"] is False
        assert identity["configuration_verified"] is False
        identity_manifest = json.loads(identity_output.read_text(encoding="utf-8"))
        assert identity_manifest["summary"]["components"] == 8
        assert identity_manifest["decision_scope"] == "system_identity_inventory_only"
        diagnosis_output = root / "failure-diagnosis.json"
        card_output = root / "failure-card.md"
        diagnosis = invoke("evidence", "diagnose", str(root / "failure-source-demo.json"),
                           "--system-identity", str(identity_output), "--output", str(diagnosis_output),
                           "--card", str(card_output), "--strict")
        assert diagnosis["primary_candidate_id"] == "candidate-harness-tool"
        assert diagnosis["root_cause_verified"] is False
        assert diagnosis["probability_estimate"] is False
        assert card_output.is_file()
        scope_root = root / "scope-project"
        (scope_root / "safe2").mkdir(parents=True)
        (scope_root / "safe2" / "app.py").write_text("value = 1\n", encoding="utf-8")
        scope_output = root / "assessment-scope.json"
        scope = invoke("evidence", "scope", str(root / "assessment-scope-source-demo.json"),
                       "--project-root", str(scope_root), "--system-identity", str(identity_output),
                       "--output", str(scope_output), "--strict")
        assert scope["summary"]["included"] == 1
        assert scope["scope_verified"] is False
        assert scope["content_inspected"] is False
    print("Installed distribution: receipts, fifteen schemas, pytest capture, harness intake, system identity, failure localization, and assessment scope passed")


if __name__ == "__main__":
    main()
