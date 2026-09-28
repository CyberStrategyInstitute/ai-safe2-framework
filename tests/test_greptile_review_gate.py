from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


SCRIPT = Path(__file__).parents[1] / "scripts" / "verify_greptile_review.py"
SPEC = spec_from_file_location("verify_greptile_review", SCRIPT)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
evaluate = MODULE.evaluate


def actor(login="greptile-apps[bot]"):
    return {"user": {"login": login}}


def test_rejects_missing_current_head_review():
    result = evaluate(
        head_sha="b" * 40,
        reviews=[actor() | {"commit_id": "a" * 40, "body": "Full prior review"}],
        issue_comments=[],
        review_comments=[],
    )
    assert not result.ok
    assert "current head" in result.reason


def test_rejects_quota_message_even_when_review_event_exists():
    review = actor() | {
        "id": 7,
        "commit_id": "b" * 40,
        "submitted_at": "2026-09-23T12:00:00Z",
        "body": "The account has reached the 50-credit limit. Upgrade your plan.",
    }
    result = evaluate(
        head_sha="b" * 40,
        reviews=[review],
        issue_comments=[],
        review_comments=[],
    )
    assert not result.ok
    assert "did not complete" in result.reason


def test_accepts_substantive_review_of_current_head():
    review = actor() | {
        "id": 7,
        "commit_id": "b" * 40,
        "submitted_at": "2026-09-23T12:00:00Z",
        "body": "Greptile review summary for this revision. " * 4,
    }
    inline = actor() | {"pull_request_review_id": 7, "body": "Validate this boundary."}
    result = evaluate(
        head_sha="b" * 40,
        reviews=[review],
        issue_comments=[],
        review_comments=[inline],
    )
    assert result.ok
    assert "1 inline" in result.reason
