import json
from pathlib import Path

from scripts.pr_agent_preflight import assess_response, eligible_candidates, select_pr_patch

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads(
    (ROOT / ".ai-safe2" / "pr-agent-preflight-policy.json").read_text(encoding="utf-8")
)


def test_catalog_filter_retains_only_configured_zero_cost_text_models():
    configured = POLICY["candidates"]
    catalog = {
        "data": [
            {
                "id": configured[0],
                "pricing": {"prompt": "0", "completion": "0"},
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": configured[1],
                "pricing": {"prompt": "0.001", "completion": "0"},
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": "unlisted/model:free",
                "pricing": {"prompt": "0", "completion": "0"},
                "architecture": {"output_modalities": ["text"]},
            },
        ]
    }

    retained, eligible_total = eligible_candidates(catalog, configured)

    assert retained == [configured[0]]
    assert eligible_total == 2


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
    files = [
        {"filename": "docs/readme.md", "patch": "docs"},
        {"filename": ".github/workflows/review.yml", "patch": "x" * 5000},
    ]

    path, patch = select_pr_patch(files, POLICY)

    assert path == ".github/workflows/review.yml"
    assert len(patch) == POLICY["pr_context"]["maximum_patch_characters"]
