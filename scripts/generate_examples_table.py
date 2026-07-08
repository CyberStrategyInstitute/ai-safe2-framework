#!/usr/bin/env python3
"""
Regenerates the examples table in README.md from the contents of examples/.

Contract, not a suggestion. Every examples/<name>/README.md MUST contain:
  <!-- stack: LangChain -->
  <!-- description: One line, no em dashes. -->

Missing either tag fails the build. No silent fallback, no "See folder README
for details" placeholder shipping to main. If a folder isn't ready to be
listed, exclude it explicitly in examples/.examples-ignore, don't half-tag it.

Usage:
    python scripts/generate_examples_table.py           # write + fail on violations
    python scripts/generate_examples_table.py --check   # dry run, fail on violations
                                                          # or on stale README, write nothing
"""

import argparse
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
README_PATH = REPO_ROOT / "README.md"
IGNORE_FILE = EXAMPLES_DIR / ".examples-ignore"

START_MARKER = "<!-- EXAMPLES:START -->"
END_MARKER = "<!-- EXAMPLES:END -->"

STACK_RE = re.compile(r"<!--\s*stack:\s*(.+?)\s*-->", re.IGNORECASE)
DESC_RE = re.compile(r"<!--\s*description:\s*(.+?)\s*-->", re.IGNORECASE)

MAX_DESCRIPTION_WORDS = 20


def load_ignore_list():
    if not IGNORE_FILE.exists():
        return set()
    names = set()
    for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.add(line)
    return names


def validate_and_read(folder: pathlib.Path, errors: list):
    readme = folder / "README.md"
    name = folder.name

    if not readme.exists():
        errors.append(f"{name}: no README.md found")
        return None

    text = readme.read_text(encoding="utf-8", errors="ignore")
    stack_match = STACK_RE.search(text)
    desc_match = DESC_RE.search(text)

    local_errors = []
    if not stack_match:
        local_errors.append(f"{name}: missing <!-- stack: ... --> tag in README.md")
    if not desc_match:
        local_errors.append(f"{name}: missing <!-- description: ... --> tag in README.md")

    if local_errors:
        errors.extend(local_errors)
        return None

    stack = stack_match.group(1).strip()
    description = desc_match.group(1).strip()

    if not stack:
        local_errors.append(f"{name}: <!-- stack: --> tag is empty")
    if not description:
        local_errors.append(f"{name}: <!-- description: --> tag is empty")
    if description and len(description.split()) > MAX_DESCRIPTION_WORDS:
        local_errors.append(
            f"{name}: description is {len(description.split())} words, "
            f"keep it under {MAX_DESCRIPTION_WORDS}"
        )
    if "—" in description or "--" in description:
        local_errors.append(f"{name}: description uses an em dash, rewrite without one")

    if local_errors:
        errors.extend(local_errors)
        return None

    return {"name": name, "stack": stack, "description": description}


def build_table(rows):
    header = "| Example | Stack | What It Governs |\n|---|---|---|\n"
    lines = []
    for row in sorted(rows, key=lambda r: r["name"]):
        link = (
            f"[`{row['name']}/`]"
            f"(https://github.com/CyberStrategyInstitute/ai-safe2-framework/tree/main/examples/{row['name']})"
        )
        lines.append(f"| {link} | {row['stack']} | {row['description']} |")
    return header + "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="dry run: validate and diff only, never write README.md"
    )
    args = parser.parse_args()

    if not EXAMPLES_DIR.exists():
        print(f"No examples/ directory found at {EXAMPLES_DIR}", file=sys.stderr)
        sys.exit(1)

    ignored = load_ignore_list()
    errors = []
    rows = []

    for folder in sorted(EXAMPLES_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if folder.name in ignored:
            continue
        meta = validate_and_read(folder, errors)
        if meta:
            rows.append(meta)

    if errors:
        print("Examples table validation failed:\n", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            f"\nFix the tags above, or add the folder to "
            f"{IGNORE_FILE.relative_to(REPO_ROOT)} if it's intentionally excluded.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not rows:
        print("No example folders found, nothing to do.")
        sys.exit(0)

    table_md = build_table(rows)
    readme_text = README_PATH.read_text(encoding="utf-8")

    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(readme_text):
        print(f"Could not find {START_MARKER} / {END_MARKER} markers in README.md", file=sys.stderr)
        sys.exit(1)

    replacement = (
        f"{START_MARKER}\n"
        "<!-- This table is auto-generated by scripts/generate_examples_table.py. "
        "Do not hand-edit between these markers; edit each example's README.md instead. -->\n\n"
        f"{table_md}\n{END_MARKER}"
    )
    new_readme_text = pattern.sub(replacement, readme_text)

    if new_readme_text == readme_text:
        print("README.md examples table already up to date.")
        sys.exit(0)

    if args.check:
        print("README.md examples table is stale (would update on a real run).", file=sys.stderr)
        sys.exit(1)

    README_PATH.write_text(new_readme_text, encoding="utf-8")
    print(f"Updated examples table with {len(rows)} example(s).")


if __name__ == "__main__":
    main()
