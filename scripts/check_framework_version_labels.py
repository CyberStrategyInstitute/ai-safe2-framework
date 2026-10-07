#!/usr/bin/env python3
"""Repository-wide guard: no stale AI SAFE² framework labels, no wrong MCP control names.

Why this exists: the v3.0 -> v3.1 migration retagged the landing pages, which
`check_repo_ux.py` checks, but left "AI SAFE2 v3.0" in shipped tool output,
templates, server prompts and examples, and left v3.0 meanings attached to
renumbered CP.5.MCP IDs (for example "MCP-12 (Swarm C2 Detection)"; v3.1 MCP-12
is Principal-Scoped State). That guard only covers 17 pages and 4 phrasings.

Rules, applied to every git-tracked text file:

  STALE_LABEL  A framework-version label naming v3.0 (for example "AI SAFE2 v3.0",
               "v3.0 controls"). Lines that also name v3.1 are comparison or
               migration statements and pass.
  MCP_NAME     "MCP-N (Title Case Name)" where the name is not the canonical v3.1
               name of MCP-N in skills/mcp/data/mcp-profile-v3.1.json.
  COMPONENT    "NEXUS vX.Y" presented as the current NEXUS component when the
               package version (NEXUS/pyproject.toml) is different. Lines that say
               legacy, compat or name a check set ("v0.3 control checks") pass.
               NEXUS-A2A protocol-spec versions are not component versions.

Exceptions live in .ai-safe2/version-label-allowlist.json, each with a reason.
An allowlisted path glob that matches no tracked file is itself an error, so the
allowlist cannot silently outlive what it excuses.

Exit 0 when clean, 1 on any finding, 2 on configuration error.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = Path(".ai-safe2/version-label-allowlist.json")
PROFILE = Path("skills/mcp/data/mcp-profile-v3.1.json")
NEXUS_PYPROJECT = Path("NEXUS/pyproject.toml")

STALE_LABEL = re.compile(
    r"(?:AI\s*SAFE(?:2|²)?|SAFE(?:2|²)|\bframework)[^\n]{0,12}?\bv3\.0\b(?!\.\d)"
    r"|\bv3\.0\s+(?:controls?|framework|compliance|skill|alignment|aligned|CP\.5|scanner|scan)\b",
    re.IGNORECASE,
)
MIGRATION_CONTEXT = re.compile(r"\bv3\.1\b")
MCP_NAMED = re.compile(r"\bMCP-(\d{1,2})\s*\((?![^)]*\d{3})([A-Z][A-Za-z0-9–\- ]{3,60})\)")
NEXUS_CLAIM = re.compile(r"(?<![-\w])NEXUS(?: remains(?: an optional)?)? v(\d+\.\d+)(?:\.\d+)?\b")
NEXUS_EXEMPT = re.compile(r"legacy|compat|control checks|v\d+\.\d+ checks|added in|introduced in|canonical message", re.IGNORECASE)
MAX_BYTES = 2_000_000


def _norm(name: str) -> str:
    name = name.replace("–", "-").lower()
    name = re.sub(r"\bcontrols?\b", "", name)
    return re.sub(r"[^a-z]+", " ", name).strip()


def name_matches(cited: str, canonical: str) -> bool:
    c, k = _norm(cited), _norm(canonical)
    return bool(c) and (k.startswith(c) or c in k)


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")
    return [p for p in out.split("\0") if p]


def path_allowed(rel: str, globs: list[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(rel, g) or (g.startswith("**/") and fnmatch.fnmatch(rel, g[3:])):
            return True
    return False


def nexus_minor(root: Path) -> str:
    m = re.search(r'^version\s*=\s*"(\d+\.\d+)', (root / NEXUS_PYPROJECT).read_text(encoding="utf-8"), re.M)
    if not m:
        raise ValueError(f"no version in {NEXUS_PYPROJECT}")
    return m.group(1)


def load_config(root: Path) -> tuple[list[str], list[re.Pattern[str]], dict[str, str]]:
    allow = json.loads((root / ALLOWLIST).read_text(encoding="utf-8"))
    for entry in allow["paths"] + allow["line_patterns"]:
        if not str(entry.get("reason", "")).strip():
            raise ValueError(f"allowlist entry without a reason: {entry}")
    globs = [e["glob"] for e in allow["paths"]]
    lines = [re.compile(e["regex"]) for e in allow["line_patterns"]]
    profile = json.loads((root / PROFILE).read_text(encoding="utf-8"))
    names = {c["id"]: c["name"] for c in profile["controls"]}
    return globs, lines, names


def scan(root: Path) -> list[str]:
    globs, line_allow, canonical = load_config(root)
    nexus = nexus_minor(root) if (root / NEXUS_PYPROJECT).exists() else None
    files = tracked_files(root)
    errors: list[str] = []

    for g in globs:
        if not any(path_allowed(f, [g]) for f in files):
            errors.append(f"{ALLOWLIST}: [STALE_ALLOWLIST] '{g}' matches no tracked file; remove it")

    for rel in files:
        if path_allowed(rel, globs):
            continue
        path = root / rel
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) > MAX_BYTES or b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", "replace")
        if "v3.0" not in text and "MCP-" not in text and "NEXUS" not in text:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(p.search(line) for p in line_allow):
                continue
            if STALE_LABEL.search(line) and not MIGRATION_CONTEXT.search(line):
                errors.append(f"{rel}:{lineno}: [STALE_LABEL] {line.strip()[:140]}")
            for num, name in MCP_NAMED.findall(line):
                want = canonical.get(f"MCP-{num}")
                if want is None:
                    errors.append(f"{rel}:{lineno}: [MCP_NAME] MCP-{num} is not a v3.1 CP.5.MCP control")
                elif not name_matches(name, want):
                    errors.append(f"{rel}:{lineno}: [MCP_NAME] MCP-{num} ({name}); v3.1 name is '{want}'")
            if nexus and not NEXUS_EXEMPT.search(line):
                for ver in NEXUS_CLAIM.findall(line):
                    if ver != nexus:
                        errors.append(f"{rel}:{lineno}: [COMPONENT] NEXUS v{ver}; current NEXUS is v{nexus}")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--summary", action="store_true", help="print per-file counts instead of every line")
    args = ap.parse_args(argv)
    try:
        errors = scan(args.root.resolve())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    if args.summary:
        counts: dict[str, int] = {}
        for e in errors:
            counts[e.split(":", 1)[0]] = counts.get(e.split(":", 1)[0], 0) + 1
        for f, n in sorted(counts.items()):
            print(f"{n:5}  {f}")
    else:
        for e in errors:
            print(e)
    print(f"framework version labels: {len(errors)} finding(s)" if errors
          else "framework version labels: clean (v3.1)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
