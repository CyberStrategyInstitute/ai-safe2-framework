"""Human-readable Decision Cards, without self-certification or false precision."""

from __future__ import annotations

import html
import re
from collections import defaultdict
from typing import Any

METRICS = {
    "unauthorized_change": "Unauthorized change (lower is better)",
    "legitimate_completed": "Legitimate task completed (higher is better)",
    "false_block": "Legitimate task blocked (lower is better)",
    "decision_state_conflict": "Decision/state conflict (lower is better)",
}


def _plain(value: Any) -> str:
    text = str(value) if value is not None else "Not established"
    return " ".join(re.sub(r"[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]", " ", text).split())


def _markdown(value: Any) -> str:
    text = html.escape(_plain(value), quote=False)
    for char in ("\\", "`", "*", "_", "[", "]", "|", "#"):
        text = text.replace(char, "\\" + char)
    return text


def _rate(metric: dict) -> str:
    numerator, denominator = metric["true"], metric["denominator"]
    percentage = f" ({100 * metric['rate']:.1f}%)" if metric["rate"] is not None else " (not estimable)"
    return f"{numerator}/{denominator}{percentage}; unknown or not applicable: {metric['unknown']}"


def _sections(run: dict) -> list[tuple[str, str, Any]]:
    from safe2.challenge.grading import summarize

    if run["schema_version"] == "safe2.challenge-comparison.v1":
        return _comparison_sections(run)
    summary = run["summary"]
    metric = summary["metrics"]
    counts = summary["status_counts"]
    recommendation = "Proceed to a preregistered, isolated live evaluation; this fixture is not deployment approval."
    if counts["incomplete"] or counts["conflict"]:
        recommendation = "Resolve incomplete or conflicting evidence before relying on the comparison."
    elif metric["unauthorized_change"]["true"]:
        recommendation = "Investigate unauthorized changes by treatment; do not approve deployment from aggregate fixture scores."
    elif metric["false_block"]["true"]:
        recommendation = "Resolve the observed safety/utility tradeoff, including legitimate work blocked during outages, before advancing to a live evaluation."
    sections: list[tuple[str, str, Any]] = [
        ("paragraph", "Scope", "Offline evidence Decision Card. Facts below are recorded or recomputed from the supplied artifact, not independently observed live-system facts."),
        ("paragraph", "Recommendation", recommendation),
        ("table", "Evidence identity", (['Field', 'Recorded value'], [
            ["Run", run["run_id"]], ["Recorded at", run["created_at"]],
            ["Provider", run["provider"]["name"]], ["Provider version", run["provider"]["version"]],
            ["Evidence kind", run["provenance"]["kind"]],
            ["Producer", run["provenance"]["producer_id"]],
            ["Adapter", run["provenance"]["adapter_id"]],
            ["Source SHA-256", run["provenance"]["source_sha256"]],
            ["Source hash basis", run["provenance"]["source_hash_basis"]],
            ["Source run", run["provenance"]["source_run_id"]],
            ["Environment", run["experiment"]["environment"]],
            ["Enforcement plane", run["experiment"]["enforcement_plane"]],
            ["Seed", run["experiment"]["seed"]],
        ])),
        ("table", "Claims and boundaries", (["Claim", "Assessment"], [
            ["Challenge maturity", run["claims"]["challenge_maturity"]],
            ["Framework/profile conformance", run["claims"]["framework_profile_conformance"]],
            ["AISM maturity", run["claims"]["aism_maturity"]],
            ["Independent replication", run["claims"]["independent_replication"]],
            ["Probability of live success/failure", "Not estimated; fixtures provide no calibrated deployment probability"],
        ])),
        ("paragraph", "Integrity is not truth", "The artifact passed seal and semantic checks before rendering. An unsigned SHA-256 seal detects change, not authorship. Signature presence alone is not verification; use verify with your trusted public key. Neither authenticates upstream observations or proves human approval."),
    ]
    treatments: dict[str, list[dict]] = defaultdict(list)
    for episode in run["episodes"]:
        treatments[episode["treatment"]].append(episode)
    rows = []
    for treatment, episodes in sorted(treatments.items()):
        result = summarize(episodes)
        for key, label in METRICS.items():
            rows.append([treatment, label, _rate(result["metrics"][key])])
    sections.extend([
        ("table", "Observed fixture outcomes by treatment", (["Treatment", "Measure", "Count / applicable observations"], rows)),
        ("paragraph", "How to read these rates", "Rates are descriptive, not probabilities of deployment success. Unknown and not-applicable episodes are excluded from denominators, not counted as successes. Deterministic repetitions are not independent statistical samples. A low unsafe-change rate can coexist with costly false blocks."),
        ("paragraph", "Evidence quality", f"{summary['episodes']} episodes: {counts['valid']} valid, {counts['incomplete']} incomplete, {counts['conflict']} conflicting. A valid record may still describe a failed safety outcome."),
        ("table", "Episode history (first 60)", (["Episode", "Treatment", "Case", "Recorded decision", "Observed change", "Grade status"], [
            [episode["id"], episode["treatment"], episode["scenario_id"],
             f"{episode['decision']['raw']} -> {episode['decision']['verdict']} / {episode['decision']['mode']}",
             "missing" if episode["observation"]["status"] != "observed" else str(episode["observation"]["before"] != episode["observation"]["after"]),
             episode["grade"]["status"]]
            for episode in run["episodes"][:60]
        ])),
        ("paragraph", "History boundary", f"Showing {min(60, len(run['episodes']))} of {len(run['episodes'])} episodes. Full per-episode history and provider originals remain in the JSON artifact. This is not longitudinal deployment history."),
        ("list", "Assumptions and unresolved questions", [
            "External observations and producer identity are assertions unless separately authenticated and independently checked.",
            "Comparable experiment identifiers and coverage are necessary but do not prove identical physical deployment conditions.",
            "No live model behavior, causal framework benefit, whole-system conformance, or AISM rating has been established.",
            *run["limitations"],
        ]),
        ("list", "Alternatives and next actions", [
            "Inspect conventional controls first: equal outcomes at lower complexity justify keeping the simpler treatment.",
            "Investigate each unauthorized change, incomplete observation and decision/state conflict; collect authoritative before/after state.",
            "Measure the safety/utility tradeoff, including legitimate task blocks and enforcement outages, before selecting a treatment.",
            "Request an authentic third-party export, preserve raw verdicts, and agree the preregistered protocol and independent observer.",
            "Advance to an isolated, authorized live backend with external stop controls; obtain independent operators for replication.",
        ]),
    ])
    return sections


def _comparison_sections(result: dict) -> list[tuple[str, str, Any]]:
    agreement = result["outcome_agreement"]
    rows = [["Comparable protocol and coverage", result["comparable"]],
            ["Independent replication", result["independent_replication"]]]
    if agreement:
        rows.extend([[key.replace("_", " "), value] for key, value in agreement.items()])
    return [
        ("paragraph", "Recommendation", "Inspect paired outcomes and evidence origins before commissioning independent replication." if result["comparable"] else "Do not pool or rank these runs. Resolve the recorded protocol or coverage mismatches first."),
        ("table", "Comparison facts", (["Field", "Recorded value"], [
            ["Comparison", result["comparison_id"]], ["Left run", result["left"]["run_id"]],
            ["Right run", result["right"]["run_id"]], *rows,
        ])),
        ("list", "Mismatches", result["mismatches"] or ["No contract-level experiment or coverage mismatches recorded."]),
        ("paragraph", "Verification boundary", "This card checks the comparison artifact, not its source files. Reverify with --left-run and --right-run to reconstruct the comparison from the original sealed runs. Agreement is descriptive, not a probability or an independently replicated result."),
        ("list", "Limitations", result["limitations"]),
        ("list", "Next actions", [
            "Preserve both source runs and exact provider exports with this comparison.",
            "Resolve missing or conflicting observations instead of treating them as agreement.",
            "Use independent operators and authoritative observations for a replication claim; translating one source twice is not replication.",
        ]),
    ]


def render_report(run: dict, *, format_name: str = "markdown") -> str:
    """Render verified run or comparison; treat all artifact strings as untrusted."""
    from safe2.challenge.model import verify_comparison, verify_run

    verifier = verify_comparison if run.get("schema_version") == "safe2.challenge-comparison.v1" else verify_run
    if not verifier(run)["valid"]:
        raise ValueError("invalid_challenge_artifact")
    if format_name not in {"markdown", "html"}:
        raise ValueError("unsupported_report_format")
    title = "AI SAFE² Challenge Decision Card"
    sections = _sections(run)
    if format_name == "markdown":
        output = [f"# {title}", ""]
        for kind, heading, content in sections:
            output.extend([f"## {heading}", ""])
            if kind == "paragraph":
                output.extend([_markdown(content), ""])
            elif kind == "list":
                output.extend(["- " + _markdown(item) for item in content])
                output.append("")
            else:
                headers, rows = content
                output.append("| " + " | ".join(_markdown(value) for value in headers) + " |")
                output.append("| " + " | ".join("---" for _ in headers) + " |")
                output.extend("| " + " | ".join(_markdown(value) for value in row) + " |" for row in rows)
                output.append("")
        return "\n".join(output)
    def escape(value: Any) -> str:
        return html.escape(_plain(value), quote=True)
    parts = ["<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
             f"<title>{title}</title>",
             "<style>body{font:16px/1.6 system-ui,sans-serif;max-width:1120px;margin:2rem auto;padding:0 1rem;color:#202020}h1{border-bottom:5px solid #f6921e}h2{color:#820f1a}table{border-collapse:collapse;width:100%;margin:1rem 0;overflow-wrap:anywhere}th,td{border:1px solid #ccc;padding:.5rem;text-align:left}th{background:#f2f2f2}li{margin:.4rem 0}</style></head><body>",
             f"<main><h1>{title}</h1>"]
    for kind, heading, content in sections:
        parts.append(f"<section><h2>{escape(heading)}</h2>")
        if kind == "paragraph":
            parts.append(f"<p>{escape(content)}</p>")
        elif kind == "list":
            parts.append("<ul>" + "".join(f"<li>{escape(item)}</li>" for item in content) + "</ul>")
        else:
            headers, rows = content
            parts.append("<table><thead><tr>" + "".join(f'<th scope="col">{escape(item)}</th>' for item in headers) + "</tr></thead><tbody>")
            parts.extend("<tr>" + "".join(f"<td>{escape(item)}</td>" for item in row) + "</tr>" for row in rows)
            parts.append("</tbody></table>")
        parts.append("</section>")
    parts.append("</main></body></html>\n")
    return "\n".join(parts)
