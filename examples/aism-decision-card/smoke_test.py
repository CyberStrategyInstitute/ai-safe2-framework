"""Self-contained acceptance check for the AISM Decision Card example."""

from __future__ import annotations

import json
from pathlib import Path

from safe2.aism.card import render_html, render_markdown
from safe2.aism.scoring import assess


def main() -> int:
    folder = Path(__file__).resolve().parent
    result = assess(json.loads((folder / "assessment.json").read_text(encoding="utf-8")))
    markdown = render_markdown(result)
    html = render_html(result)

    assert result["decision"]["disposition"] == "HOLD"
    assert result["score"]["completeness"] == 1.0
    assert result["score"]["raw"] > result["score"]["evidence_adjusted"]
    assert all(
        marker in markdown
        for marker in (
            "FACT-001",
            "ASSUMPTION-001",
            "CONFLICT-001",
            "UNKNOWN-001",
            "## History",
        )
    )
    assert all(marker in html for marker in ("History", "Material event", "Basis", "Limitations"))
    print("AISM Decision Card example: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
