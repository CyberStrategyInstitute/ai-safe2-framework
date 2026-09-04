"""Human-readable AISM Decision Card renderer."""

from __future__ import annotations

from html import escape


def _score(value: float | None) -> str:
    return "NOT ASSESSED" if value is None else f"{value:.2f}/5"


def _probability(estimate: dict) -> str:
    if estimate.get("mode") == "not_estimable":
        return f"NOT ESTIMABLE: {estimate.get('reason', 'insufficient evidence')}"
    bounds = estimate.get("range", [])
    if len(bounds) != 2:
        return "NOT ESTIMABLE"
    return (
        f"{estimate.get('outcome')}: {bounds[0]:.0%}-{bounds[1]:.0%} over "
        f"{estimate.get('time_horizon')}; complementary non-outcome: "
        f"{1 - bounds[1]:.0%}-{1 - bounds[0]:.0%} "
        f"({estimate.get('mode')}, "
        f"{estimate.get('confidence')} confidence; method: {estimate.get('method')})"
    )


def _md(value: object) -> str:
    """Keep agent-controlled values from breaking Markdown tables or injecting HTML."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def render_markdown(result: dict) -> str:
    subject = result["subject"]
    score = result["score"]
    maturity = score.get("maturity") or {}
    decision = result["decision"]
    lines = [
        f"# AISM Decision Card: {subject.get('name', subject.get('id', 'Unnamed subject'))}",
        "",
        f"> **{decision['disposition'].replace('_', ' ')}** - {decision['reason']}",
        "",
        "## Scorecard",
        "",
        f"- AISM Sovereignty Score: **{_score(score['raw'])}**",
        f"- Evidence-adjusted score: **{_score(score['evidence_adjusted'])}**",
        f"- Maturity: **{maturity.get('name', 'NOT ASSESSED')}**",
        "- Maturity vocabulary: **canonical AISM maturity-model.md levels**",
        f"- Assessment completeness: **{score['completeness']:.0%}**",
        f"- Evidence confidence: **{score['evidence_confidence']:.0%}**",
        f"- Evidence trust: **{score.get('evidence_trust', 'not supplied')}**",
        f"- Limiting pillar: **{score['limiting_pillar'] or 'not assessed'}**",
        f"- Target: **{score['target']:.2f}/5**",
        f"- ACT tier: **{subject.get('act_tier', 'not supplied')}**",
        "",
        "## Pillars",
        "",
        "| Pillar | Raw | Evidence-adjusted | Coverage |",
        "|---|---:|---:|---:|",
    ]
    for pillar in result["pillars"]:
        lines.append(
            f"| {_md(pillar['id'])} {_md(pillar['name'])} | {_score(pillar['raw_score'])} | "
            f"{_score(pillar['evidence_adjusted_score'])} | "
            f"{pillar['cells_assessed']}/{pillar['cells_total']} |"
        )

    lines += ["", "## Decision basis", ""]
    for label, key in (
        ("Facts", "facts"),
        ("Assumptions", "assumptions"),
        ("Conflicts", "conflicts"),
        ("Unknowns", "unknowns"),
    ):
        items = result[key]
        lines.append(f"### {label} ({len(items)})")
        lines.append("")
        if not items:
            lines.append("None recorded.")
        for item in items:
            ident = item.get("id", key.upper())
            text = item.get("statement") or item.get("description") or item.get("question", "")
            lines.append(f"- **{_md(ident)}:** {_md(text)}")
            for field, title in (
                ("source", "Source"), ("effect_if_false", "If false"),
                ("severity", "Severity"), ("resolution", "Resolution"),
            ):
                if item.get(field):
                    lines.append(f"  - {title}: {_md(item[field])}")
        lines.append("")

    lines += ["## Impacts", ""]
    if result["impacts"]:
        lines += ["| Perspective | Impact |", "|---|---|"]
        for impact in result["impacts"]:
            lines.append(
                f"| {_md(impact.get('perspective', 'unspecified'))} | {_md(impact.get('statement', ''))} |"
            )
    else:
        lines.append("No impacts were supplied.")

    lines += ["## Alternatives", ""]
    if not result["alternatives"]:
        lines.append("No alternatives were supplied.")
    else:
        lines += [
            "| Alternative | Pros | Cons | Why / why not | Effort | Residual risk | Outcome estimate |",
            "|---|---|---|---|---|---|---|",
        ]
        for option in result["alternatives"]:
            probability = _probability(option.get("outcome_estimate", {}))
            lines.append(
                f"| {_md(option.get('name', 'Unnamed'))} | {_md('; '.join(option.get('pros', [])) or 'not supplied')} | "
                f"{_md('; '.join(option.get('cons', [])) or 'not supplied')} | {_md(option.get('why', 'not supplied'))} | "
                f"{_md(option.get('effort', 'unknown'))} | "
                f"{_md(option.get('residual_risk', 'unknown'))} | {_md(probability)} |"
            )

    recommendation = result.get("recommendation", {})
    lines += ["", "## Recommended path", ""]
    lines.append(recommendation.get("summary", "No recommendation supplied."))
    if recommendation.get("basis"):
        lines += ["", "Basis:"] + [f"- {item}" for item in recommendation["basis"]]
    action_fields = (
        ("owner", "Owner"), ("due_date", "Due date"),
        ("next_review", "Next review"), ("exit_criteria", "Exit criteria"),
    )
    for field, title in action_fields:
        value = recommendation.get(field)
        if value:
            rendered = "; ".join(value) if isinstance(value, list) else value
            lines.append(f"- **{title}:** {_md(rendered)}")

    lines += ["", "## History", ""]
    if result["history"]:
        lines += ["| Date | Score | Decision | Material event |", "|---|---:|---|---|"]
        for event in result["history"]:
            lines.append(
                f"| {_md(event.get('date', ''))} | {_md(event.get('score', ''))} | "
                f"{_md(event.get('decision', ''))} | {_md(event.get('event', ''))} |"
            )
    else:
        lines.append("This is the first recorded assessment.")

    lines += ["", "## Limitations", ""] + [f"- {item}" for item in result["limitations"]]
    return "\n".join(lines) + "\n"


def render_html(result: dict) -> str:
    """Render a self-contained, printable baseball-card-style briefing."""
    subject = result["subject"]
    score = result["score"]
    decision = result["decision"]
    maturity = (score.get("maturity") or {}).get("name", "NOT ASSESSED")
    pillars = "".join(
        f"<tr><td>{escape(p['id'])} {escape(p['name'])}</td>"
        f"<td>{escape(_score(p['raw_score']))}</td>"
        f"<td>{escape(_score(p['evidence_adjusted_score']))}</td>"
        f"<td>{p['cells_assessed']}/{p['cells_total']}</td></tr>"
        for p in result["pillars"]
    )
    groups = "".join(
        f"<section><h2>{label} <span>{len(result[key])}</span></h2><ul>"
        + "".join(
            f"<li><strong>{escape(str(item.get('id', '')))}</strong> "
            f"{escape(str(item.get('statement') or item.get('question') or ''))}"
            + "".join(
                f"<br><small>{escape(title)}: {escape(str(item[field]))}</small>"
                for field, title in (("source", "Source"), ("effect_if_false", "If false"), ("severity", "Severity"), ("resolution", "Resolution"))
                if item.get(field)
            )
            + "</li>"
            for item in result[key]
        )
        + ("<li>None recorded.</li>" if not result[key] else "")
        + "</ul></section>"
        for label, key in (
            ("Facts", "facts"),
            ("Assumptions", "assumptions"),
            ("Conflicts", "conflicts"),
            ("Unknowns", "unknowns"),
        )
    )
    alternatives = "".join(
        f"<tr><td>{escape(str(item.get('name', '')))}</td>"
        f"<td>{escape('; '.join(item.get('pros', [])) or 'not supplied')}</td>"
        f"<td>{escape('; '.join(item.get('cons', [])) or 'not supplied')}</td>"
        f"<td>{escape(str(item.get('why', 'not supplied')))}</td>"
        f"<td>{escape(str(item.get('effort', 'unknown')))}</td>"
        f"<td>{escape(str(item.get('residual_risk', 'unknown')))}</td>"
        f"<td>{escape(_probability(item.get('outcome_estimate', {})))}</td></tr>"
        for item in result["alternatives"]
    )
    impacts = "".join(
        f"<li><strong>{escape(str(item.get('perspective', '')))}:</strong> {escape(str(item.get('statement', '')))}</li>"
        for item in result["impacts"]
    )
    recommendation = result.get("recommendation", {})
    recommendation_basis = "".join(
        f"<li>{escape(str(item))}</li>" for item in recommendation.get("basis", [])
    )
    recommendation_actions = "".join(
        f"<li><strong>{escape(title)}:</strong> {escape('; '.join(value) if isinstance(value, list) else str(value))}</li>"
        for field, title in (("owner", "Owner"), ("due_date", "Due date"), ("next_review", "Next review"), ("exit_criteria", "Exit criteria"))
        if (value := recommendation.get(field))
    )
    history = "".join(
        f"<tr><td>{escape(str(item.get('date', '')))}</td>"
        f"<td>{escape(str(item.get('score', '')))}</td>"
        f"<td>{escape(str(item.get('decision', '')))}</td>"
        f"<td>{escape(str(item.get('event', '')))}</td></tr>"
        for item in result["history"]
    )
    limitations = "".join(f"<li>{escape(str(item))}</li>" for item in result["limitations"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AISM Decision Card - {escape(str(subject.get("name", "Assessment")))}</title>
<style>
:root{{--ink:#17202a;--muted:#65717c;--red:#8b1e2d;--orange:#f6921e;--paper:#f7f4ee;--line:#d8d0c3}}
*{{box-sizing:border-box}}body{{margin:0;background:#25282d;color:var(--ink);font:15px/1.45 system-ui,sans-serif}}
main{{max-width:980px;margin:24px auto;background:var(--paper);border:8px solid var(--ink);border-radius:20px;overflow:hidden}}
header{{background:var(--ink);color:white;padding:24px}}header p{{color:#ddd}}.decision{{padding:22px;background:#fff;border-left:12px solid var(--orange)}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line)}}.stat{{background:var(--paper);padding:18px}}.stat b{{display:block;font-size:1.6rem}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:18px}}section{{background:white;border:1px solid var(--line);border-radius:10px;padding:16px}}
h1,h2{{margin:0 0 8px}}h2 span{{color:var(--muted);font-size:.8em}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid var(--line);text-align:left}}
.wide{{grid-column:1/-1}}.recommend{{border:2px solid var(--orange)}}footer{{padding:16px;color:var(--muted);font-size:.85rem}}@media(max-width:700px){{.stats,.grid{{grid-template-columns:1fr}}.wide{{grid-column:auto}}}}
@media print{{body{{background:white}}main{{margin:0;border-width:3px}}}}
</style></head><body><main>
<header><h1>{escape(str(subject.get("name", "Unnamed subject")))}</h1><p>{escape(str(subject.get("kind", "assessment")))} | {escape(str(subject.get("act_tier", "ACT tier not supplied")))}</p></header>
<div class="decision"><h2>{escape(decision["disposition"].replace("_", " "))}</h2><p>{escape(decision["reason"])}</p></div>
<div class="stats"><div class="stat">AISM score<b>{escape(_score(score["raw"]))}</b></div><div class="stat">Maturity<b>{escape(maturity)}</b></div><div class="stat">Evidence<b>{score["evidence_confidence"]:.0%}</b><small>{escape(str(score.get("evidence_trust", "")))}</small></div><div class="stat">Coverage<b>{score["completeness"]:.0%}</b></div></div>
<div class="grid"><section class="wide"><h2>Pillars</h2><table><thead><tr><th>Pillar</th><th>Raw</th><th>Evidence-adjusted</th><th>Cells</th></tr></thead><tbody>{pillars}</tbody></table></section>
{groups}<section class="wide"><h2>Impacts</h2><ul>{impacts or "<li>No impacts supplied.</li>"}</ul></section>
<section class="wide"><h2>Alternatives</h2><table><thead><tr><th>Path</th><th>Pros</th><th>Cons</th><th>Why / why not</th><th>Effort</th><th>Residual risk</th><th>Outcome estimate</th></tr></thead><tbody>{alternatives}</tbody></table></section>
<section class="wide recommend"><h2>Recommended path</h2><p>{escape(str(recommendation.get("summary", "No recommendation supplied.")))}</p><h3>Basis</h3><ul>{recommendation_basis or "<li>No basis supplied.</li>"}</ul><h3>Action</h3><ul>{recommendation_actions or "<li>No action ownership supplied.</li>"}</ul></section>
<section class="wide"><h2>History</h2><table><thead><tr><th>Date</th><th>Score</th><th>Decision</th><th>Material event</th></tr></thead><tbody>{history or '<tr><td colspan="4">First recorded assessment.</td></tr>'}</tbody></table></section>
<section class="wide"><h2>Limitations</h2><ul>{limitations or "<li>None recorded.</li>"}</ul></section></div>
<footer>AI SAFE2 v3.1 | AISM decision support | Raw score is normative; evidence-adjusted score is supplemental. Human authority retained.</footer>
</main></body></html>"""
