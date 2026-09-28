import json
from importlib.resources import files

import pytest
from click.testing import CliRunner

from safe2.cli import cli
from safe2.decision.gateway import DecisionGateway


def policy():
    return json.loads(files("safe2.data").joinpath("decision-routing-policy-v1.json").read_text())


def request(risk="high", classification="restricted"):
    return {
        "schema_version": "safe2.decision-request.v1",
        "decision_id": "case-1",
        "decision_class": "risk_signal",
        "data_classification": classification,
        "structured_state": {
            "decision_capsule": {"affected_domains": ["authorization"]},
            "api_token": "secret",
        },
        "questions": {"boundary": {"type": "noul", "instructions": "Does this affect a boundary?"}},
        "deterministic": {
            "risk_tier": risk,
            "required_evidence": ["negative-tests"],
            "evidence_status": {"negative-tests": "pending"},
            "policy_flags": {"touches_authorization": True},
        },
        "external_adjudication_allowed": True,
    }


class Fake:
    name = "kev_local"
    model = "kev-test"

    def decide(self, state, questions):
        assert state["api_token"] == "[REDACTED]"
        return {"answers": {"boundary": {"noul": 0.55}}}


def test_high_risk_never_gains_authority_and_restricted_data_stays_local():
    result = DecisionGateway(policy(), Fake(), Fake()).evaluate(request())
    assert result["review_plan"]["human_approval_required"] is True
    assert result["review_plan"]["model_may_reduce_risk"] is False
    assert result["review_plan"]["external_adjudication_eligible"] is False
    assert not any(result["authority"].values())
    assert len(result["provider_evidence"]) == 1


def test_invalid_request_fails_closed():
    value = request()
    value["decision_class"] = "merge_authorization"
    with pytest.raises(ValueError, match="violates contract"):
        DecisionGateway(policy()).evaluate(value)


def test_nested_sensitive_capsule_field_disables_external_adjudication():
    value = request(risk="medium", classification="internal_sanitized")
    value["structured_state"]["decision_capsule"] = {
        "facts": {"production_logs": "not allowed externally"}
    }
    result = DecisionGateway(policy(), Fake(), Fake()).evaluate(value)
    assert result["review_plan"]["external_adjudication_eligible"] is False
    assert result["route"]["outcome"] == "human_or_more_evidence"
    assert "production_logs" in result["route"]["external_capsule_gaps"][0]


def test_cli_replay_seed_corpus(tmp_path):
    result = CliRunner().invoke(
        cli, ["decision", "replay", ".ai-safe2/decision-evals", "-o", str(tmp_path / "report.json")]
    )
    assert result.exit_code == 0, result.output
    assert json.loads((tmp_path / "report.json").read_text())["failed"] == 0
