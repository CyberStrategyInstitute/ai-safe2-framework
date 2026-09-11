import copy
import json

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.contracts import validate_artifact
from safe2.evidence.usage import correlate_usage


def task(identifier="t1", parent=None):
    return {"schema_version": "safe2.task-receipt-input.v1", "task_id": identifier,
            "parent_task_id": parent, "harness": "harness", "criteria": [{"id": "artifact",
            "kind": "artifact_sha256", "path": "absent.txt", "expected_sha256": "0" * 64}], "usage": []}


def event(identifier="u1", value=0.1, basis="provider_reported"):
    return {"event_id": identifier, "metric": "api_cost_usd", "value": value,
            "basis": basis, "source_ref": "source"}


def test_separate_estimated_reported_unknown_and_decimal_sums():
    document = task()
    document["usage"] = [event(), event("u2", 0.2), event("u3", 0.8, "estimated"), event("u4", None, "unknown")]
    result = correlate_usage([document])
    sums = {item["basis"]: item["known_sum"] for item in result["tasks"][0]["totals"]}
    assert sums == {"provider_reported": "0.3", "estimated": "0.8", "unknown": None}
    assert result["billing_verified"] is False
    assert validate_artifact("usage-summary-v1", result) == []


def test_identical_inputs_are_deduplicated():
    document = task()
    document["usage"] = [event()]
    result = correlate_usage([document, copy.deepcopy(document)])
    assert result["unique_usage_events"] == 1
    assert result["duplicate_inputs_ignored"] == 1


def test_conflicting_task_versions_rejected():
    old, new = task(), task()
    new["usage"] = [event()]
    with pytest.raises(ValueError, match="Conflicting"):
        correlate_usage([old, new])


def test_parent_child_duplicate_event_rejected():
    parent, child = task(), task("t2", "t1")
    parent["usage"], child["usage"] = [event()], [event()]
    with pytest.raises(ValueError, match="multiple task owners"):
        correlate_usage([parent, child])


def test_cycle_rejected():
    with pytest.raises(ValueError, match="cycle"):
        correlate_usage([task("t1", "t2"), task("t2", "t1")])


def test_missing_parent_and_missing_usage_explicit():
    result = correlate_usage([task("t1", "unobserved-parent")])
    assert result["missing_parent_ids"] == ["unobserved-parent"]
    assert result["tasks"][0]["usage_present"] is False
    assert result["tasks"][0]["totals"] == []


def test_nonfinite_data_rejected():
    document = task()
    document["usage"] = [event(value=float("nan"))]
    with pytest.raises(ValueError):
        correlate_usage([document])


def test_batch_limit():
    with pytest.raises(ValueError):
        correlate_usage([task()] * 33)


def test_cli_does_not_read_or_execute_criterion_artifacts(tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(task()), encoding="utf-8")
    result = CliRunner().invoke(cli, ["feedback", "usage", str(source), str(source)])
    assert result.exit_code == 0
    assert json.loads(result.output)["duplicate_inputs_ignored"] == 1
