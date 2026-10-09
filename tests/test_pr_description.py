import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_pr_description.py"
SPEC = importlib.util.spec_from_file_location("validate_pr_description", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
validate = MODULE.validate


COMPLETE = """## Decision Summary
Decision requested.
## Problem
Problem described.
## Scope and Included Changes
Scope described.
## Evidence and Testing
Evidence described.
## Security and Evidence Boundaries
Boundary described.
## Compatibility and Recovery
Rollback described.
## Deferred and Post-Merge Work
Deferred work described.
## Owner Decision and Residual Risk
Owner decides.
"""


def test_material_description_requires_decision_context():
    assert validate(title="feat: capability", body=COMPLETE) == []
    errors = validate(title="feat: capability", body="## Summary\nOnly activities.")
    assert "missing decision section: problem" in errors
    assert "missing material-change section: compatibility and recovery" in errors


def test_literal_newline_escape_is_rejected():
    assert any("literal" in error for error in validate(title="docs: update", body=COMPLETE + "\\n"))


def test_dependency_bot_is_exempt():
    assert validate(title="build(deps): bump tool", body="", author="dependabot[bot]") == []
