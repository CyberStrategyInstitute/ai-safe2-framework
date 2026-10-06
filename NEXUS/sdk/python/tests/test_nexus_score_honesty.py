"""nexus-score must exercise behavior and never call missing evidence a pass (2026-10-06)."""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "compliance" / "scoring" / "nexus-score.py"


def run(env_extra=None, path=None):
    env = {**os.environ, **(env_extra or {})}
    env.pop("OPA_BIN", None)
    if path is not None:
        env["PATH"] = path
    return subprocess.run([sys.executable, str(SCRIPT), "--v03-checks"], capture_output=True, text=True, env=env)


def test_no_conformance_claim_and_no_silent_pass_without_opa():
    r = run(path=os.path.dirname(sys.executable))  # no opa on PATH
    assert "not a conformance claim" in r.stdout
    assert "satisfied" not in r.stdout
    assert "[?? ] AISM-OPA" in r.stdout, "missing OPA evidence must be NOT ASSESSED, not OK"
    assert r.returncode == 2


def test_guardian_and_agbom_checks_are_behavioral():
    r = run(path=os.path.dirname(sys.executable))
    assert "[OK ] S1.3-GIP" in r.stdout and "hostile denied" in r.stdout
    assert "[OK ] A2.3-AGBOM" in r.stdout and "tamper detected" in r.stdout
