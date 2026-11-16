"""Docs touched by the `--manifest` rename: documented commands must use real options.

A mechanical rename once turned `--profile` into `--manifestfile` and `--project-root` into
`--manifestject-root` in unrelated docs, and no test notices a copied command that fails.
"""

from __future__ import annotations

import re
from pathlib import Path

import click
import pytest

from safe2.cli import cli

ROOT = Path(__file__).resolve().parent.parent
DOCS = [
    ROOT / "safe2" / "README.md",
    ROOT / "safe2" / "docs" / "README.md",
    ROOT / "safe2" / "docs" / "UNIFIED-ASSESSMENT.md",
    ROOT / "safe2" / "docs" / "ASSESS-MANIFEST.md",
]
ALLOWED_MANIFEST_OPTIONS = {"--manifest", "--manifest-out"}
COMMAND_LINE = re.compile(r"^\s*(?:\|\s*)?`?(safe2 [^`]*)")
OPTION = re.compile(r"(?<![\w-])(--[a-z][a-z0-9-]*)")


def resolve(command_line: str) -> tuple[click.Command | None, list[str]]:
    """Walk `safe2 a b --opt` down the click tree; return the command and the remaining tokens."""
    command: click.Command = cli
    tokens = command_line.split()[1:]
    consumed = 0
    for token in tokens:
        if not isinstance(command, click.Group) or token not in command.commands:
            break
        command = command.commands[token]
        consumed += 1
    if consumed == 0:
        return None, tokens
    return command, tokens[consumed:]


def documented_command_lines() -> list[tuple[str, int, str]]:
    found = []
    for path in DOCS:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = COMMAND_LINE.match(line)
            if match and resolve(match.group(1))[0] is not None:
                found.append((path.relative_to(ROOT).as_posix(), number, match.group(1)))
    return found


def test_no_doc_contains_a_mangled_manifest_option() -> None:
    for path in DOCS:
        text = path.read_text(encoding="utf-8")
        mangled = [option for option in re.findall(r"--manifest[A-Za-z]\w*", text)]
        assert not mangled, f"{path.name}: {mangled}"
        assert set(re.findall(r"--manifest(?:-[a-z]+)?", text)) <= ALLOWED_MANIFEST_OPTIONS


@pytest.mark.parametrize(("path", "number", "line"), documented_command_lines())
def test_every_option_in_a_documented_safe2_command_exists(path: str, number: int, line: str) -> None:
    command, remaining = resolve(line)
    assert command is not None
    known = {opt for parameter in command.params for opt in getattr(parameter, "opts", [])}
    known |= {opt for parameter in command.params for opt in getattr(parameter, "secondary_opts", [])}
    known |= {"--help"}
    # Placeholders such as `[--strict]` and alternatives such as `--a|--b` are both options.
    unknown = sorted({option for option in OPTION.findall(" ".join(remaining)) if option not in known})
    assert not unknown, f"{path}:{number}: `{line.strip()}` uses unknown option(s) {unknown} for `{command.name}`"


def test_the_two_restored_commands_are_documented_with_their_real_options() -> None:
    readme = (ROOT / "safe2" / "README.md").read_text(encoding="utf-8")
    unified = (ROOT / "safe2" / "docs" / "UNIFIED-ASSESSMENT.md").read_text(encoding="utf-8")
    assert "safe2 init . --profile local" in readme and "safe2 init . --profile local" in unified
    assert "safe2 evidence scope SOURCE --project-root PATH" in readme
