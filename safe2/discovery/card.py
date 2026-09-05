"""Human-readable environment posture baseball card."""

from __future__ import annotations

from html import escape
from typing import Any

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _md(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "\\|")
        .replace("`", "\\`")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _model(discovery: dict[str, Any]) -> dict[str, Any]:
    posture = discovery["posture"]
    summary = discovery["summary"]
    assets = discovery.get("asset_inventory", {})
    config = discovery.get("configuration_inspection", {}).get("summary", {})
    drift = discovery.get("drift")
    findings = sorted(
        posture["findings"],
        key=lambda row: (-SEVERITY_ORDER.get(row["severity"], 0), row["id"]),
    )
    completed = summary.get("targets_completed", 0)
    requested = summary.get("explicit_targets", 0)
    confidence = "LOW"
    if config.get("completed", 0) and not summary.get("targets_failed", 0):
        confidence = "MODERATE"
    facts = _unique([fact for row in findings for fact in row.get("facts", [])])
    assumptions = _unique(
        [assumption for row in findings for assumption in row.get("assumptions", [])]
    )
    shown_findings = findings[:7]
    return {
        "title": "AI SAFE2 Environment Decision Card",
        "disposition": posture["disposition"],
        "scope": discovery["scope"].get("root", "unknown"),
        "collected_at": discovery.get("collected_at", "unknown"),
        "confidence": confidence,
        "stats": {
            "harnesses": summary.get("harnesses_detected", 0),
            "assets": len(assets.get("assets", [])),
            "targets": f"{completed}/{requested}",
            "configurations": f"{config.get('completed', 0)}/{config.get('candidates', 0)}",
            "drift": drift.get("changes", 0) if drift else "NO BASELINE",
            "findings": (
                f"{sum(row['severity'] in {'critical', 'high'} for row in findings)}/"
                f"{len(findings)} high/total"
            ),
        },
        "facts": facts,
        "assumptions": assumptions,
        "conflicts": [
            row["title"]
            for row in findings
            if row["category"] in {"configuration_drift", "coverage_drift"}
        ],
        "findings": shown_findings,
        "findings_remaining": len(findings) - len(shown_findings),
        "impacts": [
            f"Human operator: {len(findings)} findings require ownership or documented acceptance.",
            f"Agent runtime: disposition is {posture['disposition']}; autonomous promotion is not supported by this evidence.",
            "Security and governance: metadata coverage identifies review targets but does not demonstrate control effectiveness.",
        ],
        "coverage": posture["coverage"],
        "history": {
            "baseline_collected_at": drift.get("baseline_collected_at") if drift else None,
            "current_collected_at": discovery.get("collected_at"),
            "changes": drift.get("changes") if drift else None,
            "baseline_integrity": drift.get("baseline_integrity") if drift else None,
        },
        "integrity": discovery.get("integrity", {}),
        "policy_decision": discovery.get("policy_decision"),
        "limitations": posture["limitations"],
    }


def render_environment_markdown(discovery: dict[str, Any]) -> str:
    card = _model(discovery)
    stats = card["stats"]
    lines = [
        f"# {card['title']}",
        "",
        f"> **{card['disposition']}** - Human review authority retained.",
        "",
        "## At a glance",
        "",
        "| Scope | Evidence confidence | Harnesses | Assets | Targets | Config coverage | Drift | Findings |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| {_md(card['scope'])} | {card['confidence']} | {stats['harnesses']} | "
            f"{stats['assets']} | {stats['targets']} | {stats['configurations']} | "
            f"{stats['drift']} | {stats['findings']} |"
        ),
        "",
        "- Outcome probability: **NOT ESTIMABLE from metadata-only evidence**",
        (
            f"- Policy decision: **{_md(card['policy_decision']['disposition'])}**"
            if card["policy_decision"]
            else "- Policy decision: **No policy supplied**"
        ),
        f"- Collected: **{_md(card['collected_at'])}**",
        (
            f"- Evidence integrity: **sha256:"
            f"{_md(card['integrity'].get('digest', 'not available'))}** "
            f"({_md(card['integrity'].get('authenticity', 'unknown'))})"
        ),
        "",
        "## Decision basis",
        "",
    ]
    if card["policy_decision"]:
        policy = card["policy_decision"]
        lines += [
            "### Policy evaluation",
            "",
            f"- Policy: **{_md(policy['policy_id'])}**",
            f"- Decision: **{_md(policy['disposition'])}**",
        ]
        lines.extend(
            f"- Violation `{_md(item['rule'])}`: {_md(item['reason'])}"
            for item in policy["violations"]
        )
        lines.extend(
            f"- Unmet prerequisite `{_md(item['rule'])}`: {_md(item['reason'])}"
            for item in policy["unmet_prerequisites"]
        )
        lines.append("")
    lines += [f"### Facts ({len(card['facts'])})", ""]
    if card["facts"]:
        lines.extend(f"- {_md(item)}" for item in card["facts"])
    else:
        lines.append("None recorded.")
    lines += ["", f"### Assumptions ({len(card['assumptions'])})", ""]
    if card["assumptions"]:
        lines.extend(f"- {_md(item)}" for item in card["assumptions"])
    else:
        lines.append("None recorded.")
    lines += ["", f"### Evidence conflicts ({len(card['conflicts'])})", ""]
    if card["conflicts"]:
        lines.extend(f"- {_md(item)}" for item in card["conflicts"])
    else:
        lines.append("No baseline or coverage conflicts were identified by this collector.")
    lines += [
        "",
        "## Prioritized paths forward",
        "",
        "| Priority | Finding | Impact | Recommended action | Candidate controls |",
        "|---:|---|---|---|---|",
    ]
    for index, finding in enumerate(card["findings"], start=1):
        lines.append(
            f"| {index} | [{finding['severity'].upper()}] {_md(finding['title'])} | "
            f"Unresolved evidence may limit safe authorization or decision confidence. | "
            f"{_md(finding['recommendation'])} | "
            f"{_md(', '.join(finding.get('candidate_controls', [])))} |"
        )
    if not card["findings"]:
        lines.append("| 1 | No metadata-derived findings | Continue monitoring | Preserve baseline and reassess after material change. | P2 |")
    if card["findings_remaining"]:
        lines.append(
            f"| … | {card['findings_remaining']} additional lower-priority findings | "
            "Retained in the JSON evidence | Review the complete posture artifact. | — |"
        )
    lines += [
        "",
        "## Impacts",
        "",
    ]
    lines.extend(f"- {_md(item)}" for item in card["impacts"])
    lines += [
        "",
        "## Alternatives",
        "",
        "| Path | Pros | Cons | Why / why not |",
        "|---|---|---|---|",
        "| Continue unchanged | Lowest immediate effort | Unknowns and review findings remain | Use only with documented risk acceptance and monitoring. |",
        "| Remediate every indicator immediately | Fastest apparent closure | Metadata assumptions may cause wasted or harmful changes | Do not use without validating whether indicators are active and applicable. |",
        "| Validate, prioritize, then remediate | Evidence-led and adaptable | Requires owner time and targeted checks | **Recommended:** resolve coverage first, confirm facts, then address highest-impact findings. |",
        "",
        "## Recommended path",
        "",
        "Validate evidence coverage before changing the environment, then remediate confirmed findings in severity order.",
        "",
        "- **Owner:** Human owner not assigned",
        "- **First action:** Resolve incomplete or missing assessment coverage.",
        "- **Then:** Confirm which detected harnesses and assets are active and governed.",
        "- **Exit criteria:** Required targets assessed; material assumptions resolved; accepted findings assigned; baseline reviewed and retained.",
        "",
        "## History",
        "",
        f"- Baseline collected: **{_md(card['history']['baseline_collected_at'] or 'none supplied')}**",
        f"- Current evidence: **{_md(card['history']['current_collected_at'])}**",
        f"- Baseline integrity: **{_md(card['history']['baseline_integrity'] or 'not assessed')}**",
        f"- Material changes: **{_md(card['history']['changes'] if card['history']['changes'] is not None else 'not assessed')}**",
        "",
        "## Coverage and limitations",
        "",
    ]
    lines.extend(f"- `{_md(key)}`: **{_md(value)}**" for key, value in card["coverage"].items())
    lines.extend(f"- {_md(item)}" for item in card["limitations"])
    return "\n".join(lines) + "\n"


def render_environment_html(discovery: dict[str, Any]) -> str:
    """Render a self-contained, printable environment briefing."""
    card = _model(discovery)
    stats = "".join(
        f"<div class='stat'><span>{escape(key.replace('_', ' ').title())}</span>"
        f"<strong>{escape(str(value))}</strong></div>"
        for key, value in card["stats"].items()
    )
    findings = "".join(
        f"<tr><td><b>{escape(row['severity'].upper())}</b></td>"
        f"<td>{escape(str(row['title']))}</td><td>{escape(str(row['recommendation']))}</td>"
        f"<td>{escape(', '.join(row.get('candidate_controls', [])))}</td></tr>"
        for row in card["findings"]
    ) or "<tr><td colspan='4'>No metadata-derived findings.</td></tr>"
    if card["findings_remaining"]:
        findings += (
            f"<tr><td>…</td><td>{card['findings_remaining']} additional lower-priority "
            "findings</td><td>Review the complete JSON posture artifact.</td><td>—</td></tr>"
        )
    facts = "".join(f"<li>{escape(str(item))}</li>" for item in card["facts"]) or "<li>None recorded.</li>"
    assumptions = "".join(f"<li>{escape(str(item))}</li>" for item in card["assumptions"]) or "<li>None recorded.</li>"
    conflicts = "".join(f"<li>{escape(str(item))}</li>" for item in card["conflicts"]) or "<li>None identified by this collector.</li>"
    limitations = "".join(f"<li>{escape(str(item))}</li>" for item in card["limitations"])
    impacts = "".join(f"<li>{escape(str(item))}</li>" for item in card["impacts"])
    policy = card["policy_decision"]
    policy_results = ""
    if policy:
        policy_results = "<ul>" + "".join(
            f"<li><b>{escape(label)} {escape(str(item['rule']))}:</b> "
            f"{escape(str(item['reason']))}</li>"
            for label, rows in (
                ("Violation", policy["violations"]),
                ("Unmet prerequisite", policy["unmet_prerequisites"]),
            )
            for item in rows
        ) + "</ul>"
    policy_html = (
        f"<p>Policy <b>{escape(str(policy['policy_id']))}</b>: "
        f"<b>{escape(str(policy['disposition']))}</b> "
        f"({len(policy['violations'])} violations; "
        f"{len(policy['unmet_prerequisites'])} unmet prerequisites).</p>{policy_results}"
        if policy
        else "<p>No environment decision policy was supplied.</p>"
    )
    coverage = "".join(
        f"<tr><td>{escape(str(key))}</td><td>{escape(str(value))}</td></tr>"
        for key, value in card["coverage"].items()
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(card['title'])}</title><style>
:root{{--ink:#152536;--blue:#176b87;--teal:#22a699;--gold:#f2be22;--paper:#f5f7f8;--line:#d5dde3}}
*{{box-sizing:border-box}}body{{margin:0;background:#263747;color:var(--ink);font:15px/1.45 system-ui,sans-serif}}.skip{{position:absolute;left:-9999px;top:0;background:white;color:var(--ink);padding:12px;z-index:2}}.skip:focus{{left:12px;top:12px;outline:3px solid var(--gold)}}a:focus-visible{{outline:3px solid var(--gold);outline-offset:3px}}main{{max-width:1080px;margin:24px auto;background:var(--paper);border-radius:18px;overflow:hidden}}header{{padding:26px;background:linear-gradient(120deg,var(--ink),var(--blue));color:white}}header p{{margin:.35rem 0 0}}.decision{{padding:18px 26px;background:#fff7d6;border-left:12px solid var(--gold)}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line)}}.stat{{background:white;padding:16px}}.stat span,.stat strong{{display:block}}.stat strong{{font-size:1.45rem;color:var(--blue)}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:18px}}section{{background:white;border:1px solid var(--line);border-radius:10px;padding:16px}}.wide{{grid-column:1/-1}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:#e8f3f5}}footer{{padding:18px;color:#52616e}}@media(max-width:720px){{.stats,.grid{{grid-template-columns:1fr}}.wide{{grid-column:auto}}}}@media print{{body{{background:white}}main{{margin:0}}}}
</style></head><body><a class="skip" href="#decision-card">Skip to decision card</a><main id="decision-card" tabindex="-1"><header><h1>{escape(card['title'])}</h1><p>{escape(str(card['scope']))} · {escape(str(card['collected_at']))}</p></header>
<div class="decision"><h2>{escape(card['disposition'])}</h2><p>Evidence confidence: <b>{card['confidence']}</b>. Outcome probability: <b>NOT ESTIMABLE</b> from metadata-only evidence. Human review authority retained.</p>{policy_html}</div>
<div class="stats">{stats}</div><div class="grid"><section><h2>Facts</h2><ul>{facts}</ul></section><section><h2>Assumptions</h2><ul>{assumptions}</ul></section><section class="wide"><h2>Evidence conflicts</h2><ul>{conflicts}</ul></section>
<section class="wide"><h2>Prioritized paths forward</h2><table><caption>Findings ordered for human review and action</caption><thead><tr><th scope="col">Severity</th><th scope="col">Finding</th><th scope="col">Action</th><th scope="col">Controls</th></tr></thead><tbody>{findings}</tbody></table></section>
<section class="wide"><h2>Impacts</h2><ul>{impacts}</ul></section>
<section class="wide"><h2>Alternatives</h2><ol><li><b>Continue unchanged:</b> low effort, but unknowns remain; only with documented acceptance.</li><li><b>Remediate everything:</b> fast apparent closure, but metadata assumptions may misdirect work.</li><li><b>Validate, prioritize, remediate:</b> recommended evidence-led path.</li></ol></section>
<section class="wide recommend"><h2>Recommended path</h2><p>Validate evidence coverage before changing the environment, then remediate confirmed findings in severity order.</p><ul><li><b>Owner:</b> Human owner not assigned</li><li><b>First action:</b> Resolve incomplete or missing assessment coverage.</li><li><b>Then:</b> Confirm which detected harnesses and assets are active and governed.</li><li><b>Exit criteria:</b> Required targets assessed; material assumptions resolved; accepted findings assigned; baseline reviewed and retained.</li></ul></section>
<section><h2>History</h2><ul><li>Baseline: {escape(str(card['history']['baseline_collected_at'] or 'none supplied'))}</li><li>Changes: {escape(str(card['history']['changes'] if card['history']['changes'] is not None else 'not assessed'))}</li><li>Baseline integrity: {escape(str(card['history']['baseline_integrity'] or 'not assessed'))}</li></ul></section><section><h2>Limitations</h2><ul>{limitations}</ul></section><section class="wide"><h2>Coverage</h2><table><caption>Evidence surfaces included in this assessment</caption><thead><tr><th scope="col">Evidence surface</th><th scope="col">Observed coverage</th></tr></thead><tbody>{coverage}</tbody></table></section></div>
<footer>AI SAFE2 v3.1 environment decision support · Evidence integrity: sha256:{escape(str(card['integrity'].get('digest', 'not available')))} ({escape(str(card['integrity'].get('authenticity', 'unknown')))}) · No conformance claim.</footer></main></body></html>"""
