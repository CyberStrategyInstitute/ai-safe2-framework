"""Reviewable flag heuristics for `safe2 assess --manifest`, loaded from packaged data."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

HEURISTICS_FILE = "manifest-heuristics-v1.json"
HEURISTICS_SCHEMA = "safe2.manifest-heuristics.v1"
CATEGORIES = ("spawn", "memory", "send", "money", "write", "exec", "delete")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")


class HeuristicsError(ValueError):
    """Raised when the packaged heuristics are missing or structurally invalid."""


@dataclass(frozen=True)
class Heuristics:
    """Parsed heuristics plus the digest of the exact bytes they came from."""

    digest: str
    data: dict[str, Any]
    exact: dict[str, frozenset[str]]
    tokens: dict[str, frozenset[str]]
    approval_categories: dict[str, str]
    secret_assignment: re.Pattern[str]
    secret_private_key: re.Pattern[str]

    def categorize(self, tool_name: str) -> frozenset[str]:
        """Return the categories a tool name falls into (exact name or any token)."""
        found = {name for name, names in self.exact.items() if tool_name in names}
        name_tokens = tool_tokens(tool_name)
        found.update(name for name, tokens in self.tokens.items() if name_tokens & tokens)
        return frozenset(found)


def tool_tokens(name: str) -> frozenset[str]:
    """Split a tool name into lowercase tokens on punctuation and camelCase boundaries."""
    pieces = _NON_ALNUM.split(_CAMEL_BOUNDARY.sub("_", name))
    return frozenset(piece.lower() for piece in pieces if piece)


def _string_list(value: object, label: str) -> frozenset[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise HeuristicsError(f"{label} must be a list of strings")
    return frozenset(value)


def parse_heuristics(raw: bytes) -> Heuristics:
    """Validate the heuristics structure; fail closed on anything unexpected."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HeuristicsError("heuristics are not valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or data.get("schema_version") != HEURISTICS_SCHEMA:
        raise HeuristicsError(f"heuristics schema_version must be {HEURISTICS_SCHEMA}")
    categories = data.get("tool_categories")
    if not isinstance(categories, dict) or set(categories) != set(CATEGORIES):
        raise HeuristicsError(f"tool_categories must define exactly: {', '.join(CATEGORIES)}")
    for name in CATEGORIES:
        entry = categories[name]
        if not isinstance(entry, dict) or not {"exact", "tokens"} <= set(entry):
            raise HeuristicsError(f"tool_categories.{name} must define both exact and tokens")
    exact = {name: _string_list(categories[name]["exact"], f"{name}.exact") for name in CATEGORIES}
    tokens = {name: _string_list(categories[name]["tokens"], f"{name}.tokens") for name in CATEGORIES}
    approval = data.get("approval_point_categories")
    if not isinstance(approval, dict) or not all(
        isinstance(point, str) and category in CATEGORIES for point, category in approval.items()
    ):
        raise HeuristicsError("approval_point_categories must map approval points to categories")
    patterns = data.get("secret_patterns")
    if not isinstance(patterns, dict):
        raise HeuristicsError("secret_patterns is required")
    try:
        assignment = re.compile(str(patterns["assignment"]))
        private_key = re.compile(str(patterns["private_key_header"]))
    except (KeyError, re.error) as exc:
        raise HeuristicsError("secret_patterns are missing or not valid regular expressions") from exc
    return Heuristics(
        digest=hashlib.sha256(raw).hexdigest(),
        data=data,
        exact=exact,
        tokens=tokens,
        approval_categories=dict(approval),
        secret_assignment=assignment,
        secret_private_key=private_key,
    )


@lru_cache(maxsize=1)
def load_heuristics() -> Heuristics:
    """Load the packaged heuristics once per process."""
    try:
        raw = files("safe2.data").joinpath(HEURISTICS_FILE).read_bytes()
    except OSError as exc:
        raise HeuristicsError("packaged heuristics are not readable") from exc
    return parse_heuristics(raw)
