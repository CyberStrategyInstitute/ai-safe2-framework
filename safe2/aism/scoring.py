"""Faithful AISM 5-pillar by 6-dimension scoring with evidence provenance."""

from __future__ import annotations

from datetime import UTC, datetime
from statistics import fmean

from jsonschema import FormatChecker, ValidationError, validate

from .model import load_model, load_schema

RATING_POINTS = {"L": 1, "M": 2, "H": 3}


def _cell_score(metrics: dict, label: str, names: list[str]) -> tuple[dict, int]:
    ratings = {name: str(metrics.get(name)).upper() for name in names}
    invalid = [name for name, value in ratings.items() if value not in RATING_POINTS]
    if invalid:
        raise ValueError(f"{label}.{invalid[0]} must be L, M, or H")
    points = sum(RATING_POINTS[value] for value in ratings.values())
    score = (
        5 if points == 9 else 4 if points == 8 else 3 if points >= 6 else 2 if points >= 4 else 1
    )
    return ratings, score


def _evidence_summary(items: list[dict], grades: dict[str, float]) -> dict:
    recognized = [item for item in items if item.get("grade") in grades]
    categories = sorted(
        {str(item["category"]) for item in recognized if item.get("category")}
    )
    if not recognized:
        return {
            "strength": 0.0,
            "grade": "E0",
            "categories": [],
            "category_completeness": 0.0,
            "count": 0,
        }
    category_completeness = len(categories) / 3
    trust_caps = {"unverified": 0.2, "digest_verified": 0.6, "independently_verified": 1.0}
    strengths = [
        min(grades[item["grade"]], trust_caps.get(item.get("verification", "unverified"), 0.2))
        for item in recognized
    ]
    strength = fmean(strengths) * category_completeness
    nearest = min(grades, key=lambda grade: abs(grades[grade] - strength))
    verification = {
        level: sum(item.get("verification", "unverified") == level for item in recognized)
        for level in trust_caps
    }
    return {
        "strength": round(strength, 3),
        "grade": nearest,
        "categories": categories,
        "category_completeness": round(category_completeness, 3),
        "count": len(recognized),
        "verification": verification,
        "trust": "supplied/unverified"
        if verification["unverified"]
        else "verified as declared",
    }


def _maturity(score: float, model: dict) -> dict:
    for level in reversed(model["maturity_levels"]):
        if score >= level["minimum"]:
            return level
    return model["maturity_levels"][0]


def _validate_alternatives(alternatives: list[dict]) -> None:
    for index, alternative in enumerate(alternatives, start=1):
        estimate = alternative.get("outcome_estimate", {})
        mode = estimate.get("mode")
        if mode not in {"observed", "evidence_informed", "not_estimable"}:
            raise ValueError(
                f"alternative {index} outcome_estimate.mode must be observed, "
                "evidence_informed, or not_estimable"
            )
        if mode == "not_estimable":
            if not estimate.get("reason"):
                raise ValueError(
                    f"alternative {index} must explain why its outcome is not estimable"
                )
            continue
        required = ("outcome", "time_horizon", "method", "confidence", "range")
        missing = [field for field in required if not estimate.get(field)]
        if missing:
            raise ValueError(f"alternative {index} outcome estimate is missing {missing[0]}")
        bounds = estimate["range"]
        if not isinstance(bounds, list) or len(bounds) != 2 or not 0 <= bounds[0] <= bounds[1] <= 1:
            raise ValueError(
                f"alternative {index} probability range must be two values from 0 to 1"
            )


def assess(payload: dict) -> dict:
    """Calculate the documented AISM score; missing cells remain NOT_ASSESSED."""
    model = load_model()
    try:
        validate(payload, load_schema(), format_checker=FormatChecker())
    except ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path) or "assessment"
        raise ValueError(f"schema validation failed at {location}: {exc.message}") from exc
    if payload.get("schema_version", "1.0") != "1.0":
        raise ValueError("unsupported assessment schema_version; expected 1.0")
    alternatives = payload.get("alternatives", [])
    _validate_alternatives(alternatives)
    grades = model["evidence_grades"]
    supplied_cells = payload.get("cells", {})
    expected_cells = {
        f"{pillar['id']}.{dimension['id']}"
        for pillar in model["pillars"]
        for dimension in model["dimensions"]
    }
    unexpected = sorted(set(supplied_cells) - expected_cells)
    if unexpected:
        raise ValueError(f"unknown AISM assessment cell: {unexpected[0]}")
    cells = []
    for pillar in model["pillars"]:
        for dimension in model["dimensions"]:
            cell_id = f"{pillar['id']}.{dimension['id']}"
            supplied = supplied_cells.get(cell_id)
            if not supplied:
                cells.append(
                    {
                        "id": cell_id,
                        "pillar": pillar["id"],
                        "dimension": dimension["id"],
                        "status": "NOT_ASSESSED",
                        "score": None,
                        "evidence_adjusted_score": None,
                    }
                )
                continue
            ratings, score = _cell_score(
                supplied.get("metrics", {}), cell_id, model["assessment_metrics"]
            )
            evidence = _evidence_summary(supplied.get("evidence", []), grades)
            adjusted = score * (0.5 + 0.5 * evidence["strength"])
            cells.append(
                {
                    "id": cell_id,
                    "pillar": pillar["id"],
                    "dimension": dimension["id"],
                    "status": "ASSESSED",
                    "metrics": ratings,
                    "score": score,
                    "evidence_adjusted_score": round(adjusted, 2),
                    "evidence": evidence,
                }
            )

    pillar_results = []
    for pillar in model["pillars"]:
        pillar_cells = [cell for cell in cells if cell["pillar"] == pillar["id"]]
        assessed = [cell for cell in pillar_cells if cell["status"] == "ASSESSED"]
        dimension_weights = {
            dimension["id"]: dimension["weight"] for dimension in model["dimensions"]
        }
        assessed_weight = sum(dimension_weights[cell["dimension"]] for cell in assessed)
        raw = (
            sum(cell["score"] * dimension_weights[cell["dimension"]] for cell in assessed)
            / assessed_weight
            if assessed_weight
            else None
        )
        adjusted = (
            sum(
                cell["evidence_adjusted_score"] * dimension_weights[cell["dimension"]]
                for cell in assessed
            )
            / assessed_weight
            if assessed_weight
            else None
        )
        pillar_results.append(
            {
                "id": pillar["id"],
                "name": pillar["name"],
                "weight": pillar["weight"],
                "raw_score": round(raw, 2) if raw is not None else None,
                "evidence_adjusted_score": round(adjusted, 2) if adjusted is not None else None,
                "cells_assessed": len(assessed),
                "cells_total": len(pillar_cells),
            }
        )

    scored_pillars = [pillar for pillar in pillar_results if pillar["raw_score"] is not None]
    total_weight = sum(pillar["weight"] for pillar in scored_pillars)
    raw_score = (
        sum(p["raw_score"] * p["weight"] for p in scored_pillars) / total_weight
        if total_weight
        else None
    )
    adjusted_score = (
        sum(p["evidence_adjusted_score"] * p["weight"] for p in scored_pillars) / total_weight
        if total_weight
        else None
    )
    completeness = len([cell for cell in cells if cell["status"] == "ASSESSED"]) / len(cells)
    evidenced_cells = [cell for cell in cells if cell["status"] == "ASSESSED"]
    evidence_confidence = (
        fmean(cell["evidence"]["strength"] for cell in evidenced_cells) if evidenced_cells else 0.0
    )
    limiting_pillar = (
        min(scored_pillars, key=lambda pillar: pillar["raw_score"]) if scored_pillars else None
    )
    conflicts = payload.get("conflicts", [])
    critical = [item for item in conflicts if item.get("severity", "").upper() == "CRITICAL"]
    target = float(payload.get("subject", {}).get("target_score", 3.5))
    decision_basis_complete = bool(payload.get("facts")) and bool(
        payload.get("recommendation", {}).get("summary")
    )

    if raw_score is None:
        disposition, reason, maturity = "HOLD", "No AISM assessment cells were scored.", None
    else:
        maturity = _maturity(raw_score, model)
        if critical:
            disposition, reason = "HOLD", "Critical evidence conflicts require human resolution."
        elif completeness < 1:
            disposition, reason = "HOLD", "Assessment coverage is incomplete."
        elif not decision_basis_complete:
            disposition, reason = "HOLD", "Facts and a reasoned recommendation are required."
        elif adjusted_score is None or adjusted_score < target:
            disposition, reason = (
                "PROCEED_WITH_RESTRICTIONS",
                "Evidence-adjusted score is below target.",
            )
        else:
            disposition, reason = (
                "PROCEED",
                "Target score and assessment coverage requirements are met.",
            )

    return {
        "schema_version": "1.0",
        "assessment_type": "AISM_DECISION_SUPPORT",
        "normative_score": "score.raw",
        "generated_at": datetime.now(UTC).isoformat(),
        "framework": model["framework"],
        "subject": payload.get("subject", {}),
        "method": {
            "cells": "5 pillars x 6 dimensions",
            "cell_rubric": "AISM H/M/L three-metric rubric",
            "pillar_formula": "weighted average of six dimension cell scores",
            "overall_formula": "weighted average of five pillar scores",
            "maturity_vocabulary": (
                "Canonical level names from AISM/maturity-model.md; model aliases are retained "
                "in score.maturity.aliases for interoperability."
            ),
        },
        "score": {
            "raw": round(raw_score, 2) if raw_score is not None else None,
            "evidence_adjusted": round(adjusted_score, 2) if adjusted_score is not None else None,
            "scale": 5,
            "target": target,
            "maturity": maturity,
            "completeness": round(completeness, 3),
            "evidence_confidence": round(evidence_confidence, 3),
            "evidence_trust": "Evidence strength is capped unless verification provenance is supplied.",
            "limiting_pillar": limiting_pillar["id"] if limiting_pillar else None,
        },
        "decision": {"disposition": disposition, "reason": reason, "human_owned": True},
        "pillars": pillar_results,
        "cells": cells,
        "topic_diagnostics": payload.get("topics", {}),
        "facts": payload.get("facts", []),
        "assumptions": payload.get("assumptions", []),
        "conflicts": conflicts,
        "unknowns": payload.get("unknowns", []),
        "history": payload.get("history", []),
        "alternatives": alternatives,
        "impacts": payload.get("impacts", []),
        "recommendation": payload.get("recommendation", {}),
        "limitations": [
            "Evidence-adjusted scoring is a transparent decision-support extension; the raw score is normative.",
            "Probability ranges are attributed inputs; this engine does not invent outcome probabilities.",
            "Implementation evidence alone does not establish organizational maturity or conformance.",
        ],
    }
