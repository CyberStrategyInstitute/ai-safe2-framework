"""Keep NEXUS-owned documentation inside the canonical NEXUS boundary."""

import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__", "build", "dist"}


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
