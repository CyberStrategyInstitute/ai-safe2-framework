"""
safe2_guardian_component.py — AI SAFE2 v3.0 Inline DAG Node
Cyber Strategy Institute

Drop this component into any Langflow flow between a data-fetching
component (URL Fetcher, File Loader, API caller) and any Agent node
to enforce the LF-COMP surface within the DAG itself.

Installation:
  1. In Langflow, click "+" to add a component
  2. Select "Custom Component"
  3. Paste the contents of this file into the Code field
  4. The component appears as "AI SAFE2 Guardian" in your flow

Usage in DAG:
  [URL Fetcher] → [AI SAFE2 Guardian] → [Agent / Chat Input]
  [File Loader] → [AI SAFE2 Guardian] → [Prompt Template]
  [API Response] → [AI SAFE2 Guardian] → [OpenAI Agent]

The component will:
  - Block injection patterns before they reach the Agent node
  - Log violations to the Langflow component output for visibility
  - Pass clean content through unchanged
  - Return a safe error message (not the injected content) on block
"""

from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data

# Inline detection patterns (no external deps)
import re

_INJECT_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(?:previous|prior|above)\s+instructions",
    r"(?i)you\s+are\s+now\s+(?:a|an|the)\b",
    r"(?i)disregard\s+your\s+(?:training|guidelines|rules)",
    r"(?i)(?:forget|override|bypass)\s+(?:your\s+)?instructions",
    r"(?i)\[SYSTEM\]|\[OVERRIDE\]|\[ADMIN\]|\[INST\]",
    r"(?i)system\s+override",
    r"(?i)(?:exfiltrate|send\s+all|forward\s+all)\s+(?:data|inputs?|outputs?|memory)\s+to\s+https?://",
    r"(?i)(?:send|post|call)\s+(?:this|all|every)\s+(?:conversation|message|data)\s+to\s+https?://",
]

_HIDDEN_UNICODE = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad"]


def _scan_text(text: str) -> tuple[bool, str]:
    """Returns (is_clean, violation_message)."""
    for pattern in _INJECT_PATTERNS:
        if re.search(pattern, text):
            return False, f"[AI SAFE2 LF.COMP] Injection pattern detected. Content blocked before reaching Agent."

    for ch in _HIDDEN_UNICODE:
        if ch in text:
            return False, f"[AI SAFE2 LF.COMP] Hidden Unicode U+{ord(ch):04X} detected. Content blocked."

    return True, ""


class AISAFE2GuardianComponent(Component):
    display_name = "AI SAFE2 Guardian"
    description  = "AI SAFE2 v3.0 LF-COMP enforcement: scans DAG component output for injection before it reaches Agent nodes."
    icon         = "shield"
    name         = "AISAFE2Guardian"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input Text",
            info="Connect the output of a data-fetching component (URL Fetcher, File Loader, API Response) here.",
            required=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Scanned Text",
            name="output_text",
            method="scan_and_pass",
        ),
    ]

    def scan_and_pass(self) -> Data:
        text    = self.input_text
        is_safe, violation_msg = _scan_text(text)

        if is_safe:
            self.status = f"[AI SAFE2] CLEAN — content passed (len={len(text)})"
            return Data(data={"text": text})
        else:
            self.status = f"[AI SAFE2 BLOCKED] {violation_msg}"
            # Return safe placeholder — never pass injected content downstream
            blocked_msg = (
                "[AI SAFE2 GUARDIAN] Content blocked by AI SAFE2 v3.0 LF-COMP control. "
                "Injection pattern detected in upstream component output. "
                f"Violation: {violation_msg}"
            )
            return Data(data={"text": blocked_msg})
