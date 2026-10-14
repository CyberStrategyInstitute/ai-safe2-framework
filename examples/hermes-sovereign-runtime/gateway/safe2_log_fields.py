"""
AI SAFE² log-field encoder (reference copy).

The one sanctioned way to put an untrusted value into a human-readable log line.
Identical copies ship beside each standalone gateway so every example stays
self-contained; tests/test_example_security_alerts.py fails if they drift.

CodeQL treats ``encode_log_field`` as a py/log-injection barrier through the
model pack in .github/codeql/extensions/safe2-log-models. Any change to the
encoding contract below must keep that declaration true:

* the result is a single JSON string literal (quoted, ASCII only);
* CR, LF, NEL, U+2028/U+2029, other control characters and non-ASCII text are
  escaped, so a value cannot start a new log record or emit terminal controls;
* long values are truncated with an explicit marker to bound log flooding.

Canonical audit records (JSONL) keep original values; this is presentation only.
"""

import json
from typing import Any

MAX_LOG_FIELD_CHARS = 256
_TRUNCATION_MARKER = "...[truncated]"


def encode_log_field(value: Any, limit: int = MAX_LOG_FIELD_CHARS) -> str:
    """Return ``value`` as an escaped, bounded, single-line JSON string."""
    text = str(value)
    if limit > 0 and len(text) > limit:
        text = text[:limit] + _TRUNCATION_MARKER
    return json.dumps(text, ensure_ascii=True)
