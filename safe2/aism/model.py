"""Load the versioned, machine-readable AISM model shipped with the CLI."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "aism-model-v1.json"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "aism-assessment-v1.schema.json"


@lru_cache(maxsize=1)
def load_model() -> dict:
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
