from __future__ import annotations

from safe2.discovery.posture import assess_posture


def _discovery(harnesses=None, targets=None):
    return {
        "scope": {"type": "local", "root": "/repo"},
        "harnesses": harnesses or [],
        "targets": targets or [],
    }


def test_missing_project_policy_is_review_not_failure():
    result = assess_posture(
        _discovery(
            harnesses=[
                {
                    "id": "claude-code",
                    "commands": [{"command": "claude", "path": "/bin/claude"}],
                    "evidence": [{"kind": "configuration", "scope": "user", "path": "/home/u/.claude"}],
                }
            ]
        )
    )
    assert result["disposition"] == "REVIEW"
    finding = next(row for row in result["findings"] if row["id"] == "HARNESS-POLICY-CLAUDE-CODE")
    assert finding["severity"] == "medium"
    assert "may intentionally rely" in finding["assumptions"][0]


def test_failed_explicit_target_makes_coverage_incomplete():
    result = assess_posture(
        _discovery(targets=[{"id": "ssh:audit@host:22", "status": "failed", "harnesses": []}])
    )
    assert result["disposition"] == "INCOMPLETE"
    assert result["coverage"]["explicit_targets_incomplete"] == 1
    assert any(row["category"] == "coverage_gap" for row in result["findings"])


def test_multiple_harnesses_raise_consistency_review():
    harnesses = [
        {"id": "codex", "commands": [{}], "evidence": [{"scope": "project"}]},
        {"id": "grok", "commands": [{}], "evidence": [{"scope": "project"}]},
    ]
    result = assess_posture(_discovery(harnesses=harnesses))
    assert result["disposition"] == "REVIEW"
    assert any(row["id"] == "MULTI-HARNESS-CONSISTENCY" for row in result["findings"])


def test_empty_inventory_is_baseline_not_pass():
    result = assess_posture(_discovery())
    assert result["disposition"] == "BASELINE"
    assert result["findings"] == []
    assert result["coverage"]["runtime_behavior_assessed"] is False


def test_incomplete_config_and_permissive_runtime_are_visible():
    discovery = _discovery()
    discovery["configuration_inspection"] = {
        "summary": {"candidates": 2, "completed": 1, "incomplete": 1, "secret_like_keys": 1},
        "files": [
            {
                "path": ".codex/config.toml",
                "runtime_policy": {"sandbox_mode": "danger-full-access", "approval_policy": "never"},
            }
        ],
    }
    result = assess_posture(discovery)
    assert result["disposition"] == "REVIEW"
    assert any(row["id"] == "CONFIG-INSPECTION-INCOMPLETE" for row in result["findings"])
    permissive = next(row for row in result["findings"] if row["category"] == "runtime_policy")
    assert permissive["severity"] == "high"
    assert any(row["id"] == "CONFIG-SECRET-HANDLING-REVIEW" for row in result["findings"])
    assert result["coverage"]["configuration_inspection_requested"] is True
    assert result["coverage"]["configuration_contents_assessed"] is True
