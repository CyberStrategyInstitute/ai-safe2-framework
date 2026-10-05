"""Release invariants that prevent package and documentation drift."""

import re
from pathlib import Path

import nexus_sdk

NEXUS_ROOT = Path(__file__).resolve().parents[3]


def test_package_versions_are_consistent() -> None:
    metadata = (NEXUS_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project = metadata.split("[project]", 1)[1].split("[project.", 1)[0]
    name = re.search(r'^name = "([^"]+)"$', project, flags=re.MULTILINE)
    version = re.search(r'^version = "([^"]+)"$', project, flags=re.MULTILINE)

    assert name is not None and name.group(1) == "nexus-a2a-sdk"
    assert version is not None and version.group(1) == nexus_sdk.__version__


def test_release_readme_names_current_version() -> None:
    readme = (NEXUS_ROOT / "README.md").read_text(encoding="utf-8")

    assert f"# NEXUS v{nexus_sdk.__version__}" in readme
    assert f"NEXUS v{nexus_sdk.__version__}" in readme


def test_payment_gateway_is_importable_from_distribution_namespace() -> None:
    from nexus_sdk.payments import NEXUSPaymentExecutionPlane

    assert NEXUSPaymentExecutionPlane is not None
