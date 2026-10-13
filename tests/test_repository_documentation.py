"""Repository-wide documentation ownership and discovery invariants."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_topic_registry_has_unique_existing_entrypoints() -> None:
    registry = json.loads(
        (ROOT / "repository-topics.manifest.json").read_text(encoding="utf-8")
    )
    topics = registry["topics"]

    ids = [topic["id"] for topic in topics]
    roots = [topic["root"] for topic in topics]
    assert len(ids) == len(set(ids))
    assert len(roots) == len(set(roots))

    missing: list[str] = []
    for topic in topics:
        for key in ("human_entrypoint", "agent_entrypoint", "machine_entrypoint"):
            path = topic.get(key)
            if path and not (ROOT / path).exists():
                missing.append(f"{topic['id']}:{key}={path}")
    assert missing == [], "Missing topic entrypoints: " + ", ".join(missing)


def test_topic_entrypoints_are_human_scannable() -> None:
    registry = json.loads(
        (ROOT / "repository-topics.manifest.json").read_text(encoding="utf-8")
    )
    failures: list[str] = []

    for topic in registry["topics"]:
        path = ROOT / topic["human_entrypoint"]
        content = path.read_text(encoding="utf-8")
        has_h1 = bool(re.search(r"(?m)^# ", content))
        has_link = bool(re.search(r"\[[^]]+\]\([^)]+\)", content))
        has_structure = bool(re.search(r"(?m)^(?:[-*] |\d+\. |\|)", content))
        if not (has_h1 and has_link and has_structure):
            failures.append(topic["id"])

    assert failures == [], (
        "Topic entrypoints need an H1, a navigable link, and a list or table: "
        + ", ".join(failures)
    )


def test_component_manifests_stay_inside_their_topic_homes() -> None:
    for manifest_path in (
        ROOT / "NEXUS" / "nexus-docs.manifest.json",
        ROOT / "safe2" / "safe2-docs.manifest.json",
    ):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        component_root = ROOT / manifest["canonical_root"]
        for entry in manifest["entry_points"]:
            destination = (component_root / entry["path"]).resolve()
            assert destination.is_relative_to(component_root.resolve())
            assert destination.exists(), f"Missing component entrypoint: {destination}"


def test_shared_docs_do_not_regain_cli_or_nexus_primary_pages() -> None:
    misplaced: list[str] = []
    cli_heading = re.compile(
        r"^# .*\b(?:SAFE² CLI|SAFE2 CLI|Challenge CLI)\b|"
        r"^# (?:Provider-Neutral Adapter SDK|Codex JSONL Evidence Adapter|"
        r"OpenTelemetry Evidence Interoperability|Installation Self-Check|"
        r"Unified Project Assessment)$",
        re.IGNORECASE,
    )

    for page in (ROOT / "docs").glob("*.md"):
        heading = next(
            (line.strip() for line in page.read_text(encoding="utf-8").splitlines() if line.startswith("# ")),
            "",
        )
        if heading.casefold().startswith("# nexus") or cli_heading.match(heading):
            misplaced.append(page.relative_to(ROOT).as_posix())

    assert misplaced == [], "Topic-owned pages found in shared docs: " + ", ".join(misplaced)


def test_aism_assessment_discovery_stays_in_aism() -> None:
    manifest = json.loads((ROOT / "ai-safe2.manifest.json").read_text(encoding="utf-8"))
    review = manifest["discovery"]["technology_review"]
    for key in (
        "home", "assessment_guide", "evidence_request", "entrypoint",
        "evidence_assurance", "card_template", "validation", "incident_evidence", "repo_review",
    ):
        path = ROOT / review[key]
        assert path.resolve().is_relative_to((ROOT / "AISM").resolve())
        assert path.is_file(), f"Missing AISM assessment document: {path}"

    for name in (
        "TECHNOLOGY-CONTRIBUTION-PROFILE.md", "EVIDENCE-ASSURANCE.md",
        "TECHNOLOGY-VALIDATION.md", "INCIDENT-EVIDENCE.md", "TECHNOLOGY-PROFILE-REPO-REVIEW.md",
        "templates/TECHNOLOGY-CARD.md",
    ):
        assert not (ROOT / "docs" / name).exists(), f"Competing AISM document in docs: {name}"


def test_consolidated_documentation_local_links_resolve() -> None:
    pages = list((ROOT / "safe2" / "docs").glob("*.md"))
    pages.extend((ROOT / "AISM").rglob("*.md"))
    pages.extend(
        [
            ROOT / "docs" / "README.md",
            ROOT / "guides" / "README.md",
            ROOT / "releases" / "README.md",
        ]
    )
    markdown_link = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    html_link = re.compile(r'href="([^"]+)"')
    missing: list[str] = []

    for page in pages:
        content = page.read_text(encoding="utf-8")
        targets = markdown_link.findall(content) + html_link.findall(content)
        for target in targets:
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path = target.split("#", 1)[0]
            if path:
                destination = (page.parent / path).resolve()
                if not destination.exists() or (
                    destination.is_dir() and not any(destination.iterdir())
                ):
                    missing.append(f"{page.relative_to(ROOT).as_posix()} -> {target}")

    assert missing == [], "Broken consolidated documentation links: " + ", ".join(missing)
