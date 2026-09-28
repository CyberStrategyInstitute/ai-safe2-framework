from scripts.build_review_evidence import classify, render


def policy():
    return {
        "default_tier": "low",
        "rules": [{"id": "release", "tier": "critical", "patterns": [".github/workflows/**"],
                   "reason": "release boundary", "required_evidence": ["tests"],
                   "review_lenses": ["supply-chain"]}],
        "greptile": {"recommend_for": ["critical"]},
    }


def test_classifier_escalates_and_deduplicates_evidence():
    result = classify([".github/workflows/publish.yml", "README.md"], policy())
    assert result["tier"] == "critical"
    assert result["required_evidence"] == ["tests"]
    assert result["greptile"]["recommended"] is True


def test_renderer_does_not_claim_missing_history_is_zero():
    value = {
        "subject": {"head_revision": "head", "base_revision": "base"},
        "risk": {"tier": "low", "matched_rules": [], "required_evidence": [],
                 "review_lenses": [], "greptile": {"recommended": False, "reason": "routine"}},
        "decision": {"status": "review", "gaps": ["No checks"]},
        "change": {"summary": {"files": 1, "additions": 2, "deletions": 1, "binary_files": 0}},
        "checks": [],
        "finding_history": {"reason": "No comparable prior structured finding set was supplied."},
    }
    text = render(value)
    assert "No comparable prior structured finding set" in text
    assert "No outcomes supplied" in text
