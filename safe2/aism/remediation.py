"""Evidence-bound AISM remediation planning without automatic authorization."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from importlib.resources import files
from typing import Any

from safe2.challenge.io import parse_json
from safe2.contracts import validate_artifact

from .scoring import assess


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ids(items: list[dict[str, Any]]) -> set[str]:
    return {str(item["id"]) for item in items if item.get("id")}


def _unique_ids(items: list[dict[str, Any]], label: str) -> set[str]:
    identifiers = _ids(items)
    if len(identifiers) != len(items):
        raise ValueError(f"{label} identifiers must be present and unique")
    return identifiers


def _control_ids() -> set[str]:
    document = json.loads(files("safe2.data").joinpath("ai-safe2-controls-v3.0.json").read_text())
    controls = document["pillar_controls"] + document["cross_pillar_controls"]
    return {str(item["id"]) for item in controls}


def _evidence_ids(
    assessment: dict[str, Any], identity: dict[str, Any], scope: dict[str, Any]
) -> set[str]:
    result = _ids(assessment.get("facts", [])) | _ids(assessment.get("conflicts", []))
    result |= _ids(assessment.get("unknowns", []))
    for cell in assessment.get("cells", {}).values():
        if not cell:
            continue
        for evidence in cell.get("evidence", []):
            for field in ("artifact_id", "source"):
                if evidence.get(field):
                    result.add(str(evidence[field]))
    result |= {str(item["evidence_id"]) for item in identity.get("evidence_refs", [])}
    source = scope.get("source", {})
    for field in ("scope_id", "sha256"):
        if source.get(field):
            result.add(str(source[field]))
    return result


def _dependency_order(actions: list[dict[str, Any]]) -> None:
    action_ids = _unique_ids(actions, "Remediation action")
    sequences = [item["sequence"] for item in actions]
    if len(set(sequences)) != len(sequences):
        raise ValueError("Remediation action sequence values must be unique")
    graph = {item["id"]: set(item["dependencies"]) for item in actions}
    if any(dependency not in action_ids for values in graph.values() for dependency in values):
        raise ValueError("Every remediation dependency must reference a declared action")
    if any(item_id in values for item_id, values in graph.items()):
        raise ValueError("A remediation action cannot depend on itself")
    sequence = {item["id"]: item["sequence"] for item in actions}
    if any(
        sequence[dependency] >= sequence[item_id]
        for item_id, values in graph.items()
        for dependency in values
    ):
        raise ValueError("A remediation dependency must have an earlier sequence")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visiting:
            raise ValueError("Remediation action dependencies contain a cycle")
        if item_id in visited:
            return
        visiting.add(item_id)
        for dependency in graph[item_id]:
            visit(dependency)
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in graph:
        visit(item_id)


def _gaps(scored: dict[str, Any]) -> list[dict[str, Any]]:
    target = scored["score"]["target"]
    gaps = []
    for cell in scored["cells"]:
        if cell["status"] == "NOT_ASSESSED":
            gaps.append(
                {"cell": cell["id"], "type": "not_assessed", "score": None, "target": target}
            )
        elif cell["evidence_adjusted_score"] < target:
            gaps.append(
                {
                    "cell": cell["id"],
                    "type": "below_target",
                    "score": cell["evidence_adjusted_score"],
                    "target": target,
                }
            )
    return gaps


def _history(
    previous: dict[str, Any] | None, actions: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    if previous is None:
        return [], False
    prior = {item["id"]: item for item in previous.get("actions", [])}
    history = list(previous.get("history", []))[-1000:]
    regression = False
    for action in actions:
        old = prior.get(action["id"])
        if old and old.get("status") != action["status"]:
            if old.get("status") == "completed" and action["status"] != "completed":
                regression = True
            history.append(
                {
                    "recorded_at": datetime.now(UTC).isoformat(),
                    "action_id": action["id"],
                    "from": old.get("status"),
                    "to": action["status"],
                    "basis": "current source declaration; completion evidence re-evaluated",
                }
            )
    return history[-1000:], regression


def build(
    source_data: bytes,
    assessment_data: bytes,
    identity_data: bytes,
    scope_data: bytes,
    previous_data: bytes | None = None,
) -> dict[str, Any]:
    """Build a traceable plan while keeping scoring and authorization separate."""
    source = parse_json(source_data)
    assessment = parse_json(assessment_data)
    identity = parse_json(identity_data)
    scope = parse_json(scope_data)
    previous = parse_json(previous_data) if previous_data is not None else None
    if validate_artifact("aism-remediation-source-v1", source):
        raise ValueError("AISM remediation source violates its evidence contract")
    if validate_artifact("aism-assessment-v1", assessment):
        raise ValueError("AISM assessment violates its evidence contract")
    if validate_artifact("system-identity-manifest-v1", identity):
        raise ValueError("System identity violates its evidence contract")
    if validate_artifact("assessment-scope-manifest-v1", scope):
        raise ValueError("Assessment scope violates its evidence contract")
    if previous is not None and validate_artifact("aism-remediation-plan-v1", previous):
        raise ValueError("Previous remediation plan violates its evidence contract")

    actual = {
        "assessment_sha256": _digest(assessment_data),
        "system_identity_sha256": _digest(identity_data),
        "assessment_scope_sha256": _digest(scope_data),
    }
    if source["bindings"] != actual:
        raise ValueError("Remediation source bindings do not match supplied artifacts")
    subject_id = source["subject_id"]
    if assessment["subject"]["id"] != subject_id:
        raise ValueError("Assessment subject does not match remediation subject")
    if (
        identity["subject"]["subject_id"] != subject_id
        or scope["subject"]["subject_id"] != subject_id
    ):
        raise ValueError("Identity and scope subjects must match the remediation subject")
    if scope["subject"]["system_fingerprint_sha256"] != identity["system_fingerprint_sha256"]:
        raise ValueError("Assessment scope is not bound to the supplied system identity")
    if previous is not None and (
        previous.get("plan_id") != source["plan_id"]
        or previous.get("subject", {}).get("id") != subject_id
    ):
        raise ValueError("Previous plan identity does not match the current plan")

    actions = sorted(source["actions"], key=lambda item: item["sequence"])
    _dependency_order(actions)
    controls = _control_ids()
    cells = {f"P{pillar}.D{dimension}" for pillar in range(1, 6) for dimension in range(1, 7)}
    evidence = _evidence_ids(assessment, identity, scope)
    source_assumptions = _unique_ids(source["assumptions"], "Remediation assumption")
    alternatives = _unique_ids(source["alternatives"], "Remediation alternative")
    accepted_risks = _unique_ids(source["accepted_residual_risks"], "Accepted residual risk")
    assumptions = _ids(assessment.get("assumptions", [])) | source_assumptions
    for risk in source["accepted_residual_risks"]:
        if not set(risk["evidence_refs"]) <= evidence:
            raise ValueError(f"Accepted residual risk {risk['id']} cites unavailable evidence")
    for action in actions:
        if not set(action["control_refs"]) <= controls:
            raise ValueError(f"Action {action['id']} references an unknown AI SAFE2 control")
        if not set(action["aism_cells"]) <= cells:
            raise ValueError(f"Action {action['id']} references an unknown AISM cell")
        if not set(action["evidence_refs"]) <= evidence:
            raise ValueError(f"Action {action['id']} references unavailable evidence")
        if not set(action["assumption_refs"]) <= assumptions:
            raise ValueError(f"Action {action['id']} references an unstated assumption")
        if not set(action["alternative_refs"]) <= alternatives:
            raise ValueError(f"Action {action['id']} references an unknown alternative")
        if action["status"] == "completed":
            if not action["completion_evidence_refs"]:
                raise ValueError(f"Completed action {action['id']} requires completion evidence")
            if not set(action["completion_evidence_refs"]) <= evidence:
                raise ValueError(
                    f"Completed action {action['id']} cites unavailable completion evidence"
                )
        if (
            action["status"] == "accepted_risk"
            and action["residual_risk_ref"] not in accepted_risks
        ):
            raise ValueError(
                f"Accepted-risk action {action['id']} requires a declared residual risk"
            )

    scored = assess(assessment)
    gaps = _gaps(scored)
    for gap in gaps:
        gap["action_ids"] = [item["id"] for item in actions if gap["cell"] in item["aism_cells"]]
    history, regression = _history(previous, actions)
    scope_unsafe = bool(
        scope["summary"]["unsafe_links"]
        or scope["summary"]["conflicts"]
        or scope["summary"]["truncated"]
        or scope["summary"]["unclassified"]
    )
    critical_conflict = any(
        item.get("severity", "").upper() == "CRITICAL" for item in assessment.get("conflicts", [])
    )
    uncovered = [item for item in gaps if not item["action_ids"]]
    open_actions = [
        item for item in actions if item["status"] not in {"completed", "accepted_risk"}
    ]
    blocked = [item for item in actions if item["status"] == "blocked"]
    if scope_unsafe or critical_conflict or regression or blocked:
        gate = "hold"
        reason = "A scope, conflict, dependency, or completion-regression blocker requires human resolution."
    elif uncovered or open_actions or gaps:
        gate = "review"
        reason = "Gaps or open remediation actions remain for human review."
    else:
        gate = "ready_for_human_decision"
        reason = "No supplied AISM gap or open remediation action remains; authorization stays human-owned."

    result = {
        "schema_version": "safe2.aism-remediation-plan.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "plan_id": source["plan_id"],
        "subject": assessment["subject"],
        "decision_owner": source["decision_owner"],
        "source": {
            "sha256": _digest(source_data),
            "bytes": len(source_data),
            "authentication": "not_checked",
        },
        "bindings": {
            **actual,
            "system_fingerprint_sha256": identity["system_fingerprint_sha256"],
            "scope_id": scope["source"]["scope_id"],
        },
        "assessment": {
            "raw_score": scored["score"]["raw"],
            "evidence_adjusted_score": scored["score"]["evidence_adjusted"],
            "target": scored["score"]["target"],
            "completeness": scored["score"]["completeness"],
            "maturity": scored["score"]["maturity"],
            "normative_score_unchanged": True,
        },
        "gaps": gaps,
        "assumptions": source["assumptions"],
        "actions": actions,
        "alternatives": source["alternatives"],
        "accepted_residual_risks": source["accepted_residual_risks"],
        "history": history,
        "summary": {
            "gaps": len(gaps),
            "uncovered_gaps": len(uncovered),
            "actions": len(actions),
            "open_actions": len(open_actions),
            "completed_actions": sum(item["status"] == "completed" for item in actions),
            "blocked_actions": len(blocked),
            "accepted_risks": len(source["accepted_residual_risks"]),
        },
        "decision": {
            "gate": gate,
            "reason": reason,
            "human_owned": True,
            "remediation_authorized": False,
            "conformance_claim": False,
        },
        "limitations": [
            "The plan validates supplied traceability; it does not prove implementation or authorize remediation.",
            "Completion evidence remains attributed input and does not automatically change the normative AISM score.",
            "A hash binds bytes but does not authenticate the collector, owner, or truth of a claim.",
            "Implementation evidence alone does not establish organizational maturity, certification, or AI SAFE2 conformance.",
            "Probabilities are not generated by this workflow; alternatives retain only supplied facts and rationale.",
        ],
    }
    if validate_artifact("aism-remediation-plan-v1", result):
        raise ValueError("AISM remediation planning produced an invalid plan")
    return result


def _md(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def render_markdown(plan: dict[str, Any]) -> str:
    """Render a human card from the canonical remediation plan."""
    decision = plan["decision"]
    summary = plan["summary"]
    lines = [
        f"# AISM Remediation Card: {_md(plan['subject'].get('name', plan['subject']['id']))}",
        "",
        f"> **{decision['gate'].upper().replace('_', ' ')}** - {_md(decision['reason'])}",
        "",
        "## Baseball card",
        "",
        f"- Decision owner: **{_md(plan['decision_owner'])}**",
        f"- Normative AISM score: **{plan['assessment']['raw_score']}**",
        f"- Evidence-adjusted score: **{plan['assessment']['evidence_adjusted_score']}**",
        f"- Coverage: **{plan['assessment']['completeness']:.0%}**",
        f"- Gaps: **{summary['gaps']}**; uncovered: **{summary['uncovered_gaps']}**",
        f"- Actions: **{summary['actions']}**; open: **{summary['open_actions']}**; blocked: **{summary['blocked_actions']}**",
        "- Remediation authorized: **false**",
        "- Conformance claim: **false**",
        "",
        "## Recommended sequence",
        "",
        "| # | Action | Priority | Status | Owner | Why | Why not | Dependencies | Exit criteria | Residual risk |",
        "|---:|---|---|---|---|---|---|---|---|---|",
    ]
    for action in plan["actions"]:
        lines.append(
            f"| {action['sequence']} | {_md(action['title'])} | {action['priority']} | {action['status']} | {_md(action['owner'])} | "
            f"{_md(action['why'])} | {_md(action['why_not'])} | {_md(', '.join(action['dependencies']) or 'none')} | "
            f"{_md('; '.join(action['exit_criteria']))} | {_md(action['residual_risk'])} |"
        )
    lines += [
        "",
        "## Gaps and traceability",
        "",
        "| AISM cell | Gap | Score | Target | Actions |",
        "|---|---|---:|---:|---|",
    ]
    for gap in plan["gaps"]:
        lines.append(
            f"| {gap['cell']} | {gap['type']} | {_md(gap['score'])} | {gap['target']} | {_md(', '.join(gap['action_ids']) or 'none')} |"
        )
    lines += ["", "## Assumptions", ""]
    if plan["assumptions"]:
        for item in plan["assumptions"]:
            lines += [
                f"- **{_md(item['id'])}:** {_md(item['statement'])}",
                f"  - If false: {_md(item['effect_if_false'])}",
            ]
    else:
        lines.append("No remediation-specific assumptions were supplied.")
    lines += ["", "## Alternatives", ""]
    if plan["alternatives"]:
        lines += ["| Alternative | Pros | Cons | Why not selected |", "|---|---|---|---|"]
        for item in plan["alternatives"]:
            lines.append(
                f"| {_md(item['name'])} | {_md('; '.join(item['pros']))} | {_md('; '.join(item['cons']))} | {_md(item['reason_not_selected'])} |"
            )
    else:
        lines.append("No alternatives were supplied.")
    lines += ["", "## Accepted residual risk", ""]
    if plan["accepted_residual_risks"]:
        for item in plan["accepted_residual_risks"]:
            lines.append(
                f"- **{_md(item['id'])}:** {_md(item['statement'])} (owner: {_md(item['owner'])}; review: {item['review_date']})"
            )
    else:
        lines.append("No accepted residual risks were supplied.")
    lines += ["", "## History", ""]
    if plan["history"]:
        lines += ["| Recorded | Action | From | To |", "|---|---|---|---|"]
        for item in plan["history"]:
            lines.append(
                f"| {_md(item['recorded_at'])} | {_md(item['action_id'])} | {_md(item['from'])} | {_md(item['to'])} |"
            )
    else:
        lines.append("This is the first recorded plan state.")
    lines += ["", "## Limitations", ""] + [f"- {_md(item)}" for item in plan["limitations"]]
    return "\n".join(lines) + "\n"
