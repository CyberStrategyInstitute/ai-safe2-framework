"""Keep the flagship multi-environment decision workflow inside the release gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def test_environment_decision_card_smoke(tmp_path: Path):
    script = Path("examples/environment-decision-card/smoke_test.py").resolve()
    spec = importlib.util.spec_from_file_location("safe2_environment_example", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module._run(tmp_path / "validation-output")
    assert result["policy_decision"] == "DENY"
    assert result["drift_changes"] >= 1
    assert result["manifest_invalid"] == 0
