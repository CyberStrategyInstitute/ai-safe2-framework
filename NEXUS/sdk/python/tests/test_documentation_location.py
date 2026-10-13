"""Keep NEXUS-owned documentation inside the canonical NEXUS boundary."""

import json
import os
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__", "build", "dist"}
NEXUS_ROOT = REPOSITORY_ROOT / "NEXUS"


def _is_challenge_local_evidence(relative: str) -> bool:
    return relative.startswith("challenges/") and "/controls/nexus/" in relative


def test_nexus_titled_pages_live_under_nexus() -> None:
    misplaced: list[str] = []

    pages: list[Path] = []
    for root, directories, filenames in os.walk(REPOSITORY_ROOT):
        directories[:] = [
            name
            for name in directories
            if name not in IGNORED_DIRECTORIES and not name.startswith("_nexus_")
        ]
        pages.extend(Path(root) / name for name in filenames if name.endswith(".md"))

    for page in pages:
        relative = page.relative_to(REPOSITORY_ROOT).as_posix()
        if relative.startswith("NEXUS/") or _is_challenge_local_evidence(relative):
            continue

        try:
            first_heading = next(
                line.strip()
                for line in page.read_text(encoding="utf-8").splitlines()
                if line.startswith("# ")
            )
        except (StopIteration, UnicodeDecodeError):
            continue

        if first_heading.casefold().startswith("# nexus"):
            misplaced.append(relative)

    assert misplaced == [], (
        "NEXUS-titled documentation must live under NEXUS/: "
        + ", ".join(sorted(misplaced))
    )


def test_nexus_machine_manifest_points_to_existing_resources() -> None:
    manifest = json.loads(
        (NEXUS_ROOT / "nexus-docs.manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["component"] == "NEXUS"
    assert manifest["component_version"] == "0.6.0"
    assert manifest["production_assurance"] is False
    assert {entry["audience"] for entry in manifest["entry_points"]} >= {
        "all",
        "human",
        "agent",
        "developer",
        "security-reviewer",
        "operator",
    }

    paths = [entry["path"] for entry in manifest["entry_points"]]
    gateway = manifest["payment_gateway"]
    paths.extend(value for key, value in gateway.items() if key != "status")
    missing = [path for path in paths if not (NEXUS_ROOT / path).exists()]
    assert missing == [], "Manifest paths do not exist: " + ", ".join(missing)


def test_nexus_navigation_local_links_resolve() -> None:
    checked = [
        NEXUS_ROOT / "DOCUMENTATION.md",
        NEXUS_ROOT / "llms.txt",
        NEXUS_ROOT / "payments" / "SOVEREIGN-GATEWAY.md",
        NEXUS_ROOT / "payments" / "CONTROLS.md",
    ]
    missing: list[str] = []
    link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")

    def anchors(page: Path) -> set[str]:
        found: set[str] = set()
        for line in page.read_text(encoding="utf-8").splitlines():
            if not line.startswith("#"):
                continue
            heading = line.lstrip("#").strip().casefold()
            heading = re.sub(r"[^\w\s-]", "", heading)
            found.add(re.sub(r"\s", "-", heading))
        return found

    for page in checked:
        for target in link_pattern.findall(page.read_text(encoding="utf-8")):
            if "://" in target:
                continue
            path, _, fragment = target.partition("#")
            destination = (page.parent / path).resolve() if path else page
            if path and not destination.exists():
                missing.append(f"{page.relative_to(REPOSITORY_ROOT)} -> {target}")
                continue
            if fragment and destination.is_file() and fragment not in anchors(destination):
                missing.append(
                    f"{page.relative_to(REPOSITORY_ROOT)} -> missing anchor {target}"
                )

    assert missing == [], "Broken NEXUS navigation links: " + ", ".join(missing)
