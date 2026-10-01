import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.pr_agent_preflight import (
    assess_response,
    eligible_candidates,
    endpoint_health,
    select_pr_patch,
    shortlist_by_health,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads(
    (ROOT / ".ai-safe2" / "pr-agent-preflight-policy.json").read_text(encoding="utf-8")
)


def test_catalog_filter_retains_only_configured_zero_cost_text_models():
    configured = POLICY["candidate_pool"]
    catalog = {
        "data": [
            {
                "id": configured[0],
                "pricing": {"prompt": "0", "completion": "0", "request": "0"},
                "context_length": 1000000,
                "expiration_date": "2026-10-05T00:00:00Z",
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": configured[1],
                "pricing": {"prompt": "0.001", "completion": "0"},
                "context_length": 262144,
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": "unlisted/model:free",
                "pricing": {"prompt": "0", "completion": "0"},
                "context_length": 262144,
                "architecture": {"output_modalities": ["text"]},
            },
        ]
    }

    retained, eligible_total = eligible_candidates(
        catalog,
        configured,
        16000,
        datetime(2026, 10, 1, tzinfo=UTC),
    )

    assert [model["id"] for model in retained] == [configured[0]]
    assert eligible_total == 2


def test_health_shortlist_uses_live_status_and_recent_uptime():
    model = {"id": "stealth/space-bunny-alpha", "expiration_date": "2026-10-05"}
    health = endpoint_health(
        model,
        {
            "data": {
                "endpoints": [
                    {
                        "provider_name": "Stealth",
                        "status": 0,
                        "pricing": {"prompt": "0", "completion": "0"},
                        "uptime_last_5m": 99.9,
                        "uptime_last_30m": 99.8,
                        "uptime_last_1d": 99.7,
                    }
                ]
            }
        },
    )
    alternatives = [
        health,
        {"model": "nvidia/ultra:free", "online": True, "recent_uptime": 97.0},
        {"model": "nvidia/super:free", "online": False, "recent_uptime": 91.0},
        {"model": "nvidia/nano:free", "online": True, "recent_uptime": 50.0},
    ]

    assert health["recent_uptime"] == 99.9
    assert shortlist_by_health(
        alternatives,
        size=3,
        minimum_recent_uptime=75,
    ) == [
        "stealth/space-bunny-alpha",
        "nvidia/ultra:free",
        "nvidia/super:free",
    ]


def test_canary_requires_both_defects_and_no_safe_false_positive():
    passing = json.dumps(
        {
            "canary_findings": [
                {
                    "defect_id": "authorization-after-read",
                    "line_id": "C2",
                    "why": "Sensitive bytes are read before C3 authorizes the owner.",
                },
                {
                    "defect_id": "path-traversal",
                    "line_id": "C2",
                    "why": "An untrusted stored filename can escape root.",
                },
            ],
            "safe_line_findings": [],
            "pr_context": {"path": "x.py", "potential_issue": None, "why": "insufficient evidence"},
        }
    )
    result = assess_response(passing, POLICY)
    assert result["passed"] is True
    assert result["score"] == 100
    assert result["response_characters"] == len(passing)

    unsafe = json.loads(passing)
    unsafe["safe_line_findings"] = [{"line_id": "S3", "why": "invented"}]
    result = assess_response(json.dumps(unsafe), POLICY)
    assert result["passed"] is False
    assert result["score"] == 80


def test_canary_rejects_malformed_or_incomplete_answers():
    assert assess_response("OK", POLICY)["passed"] is False
    incomplete = {
        "canary_findings": [
            {"defect_id": "path-traversal", "line_id": "C2", "why": "escape"}
        ],
        "safe_line_findings": [],
    }
    assert assess_response(json.dumps(incomplete), POLICY)["passed"] is False


def test_pr_patch_selection_prefers_security_sensitive_paths_and_bounds_content():
    limit = POLICY["pr_context"]["maximum_patch_characters"]
    files = [
        {"filename": "docs/readme.md", "patch": "docs"},
        {"filename": ".github/workflows/review.yml", "patch": "x" * (limit + 100)},
    ]

    path, patch = select_pr_patch(files, POLICY)

    assert path == ".github/workflows/review.yml"
    assert len(patch) == limit
