"""Release invariants that prevent package and documentation drift."""

from pathlib import Path

import nexus_sdk
import tomllib

NEXUS_ROOT = Path(__file__).resolve().parents[3]


def test_package_versions_are_consistent() -> None:
    metadata = tomllib.loads((NEXUS_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "nexus-a2a-sdk"
    assert metadata["project"]["version"] == nexus_sdk.__version__


def test_release_readme_names_current_version() -> None:
    readme = (NEXUS_ROOT / "README.md").read_text(encoding="utf-8")

    assert f"# NEXUS v{nexus_sdk.__version__}" in readme
    assert f"NEXUS v{nexus_sdk.__version__}" in readme


def test_payment_gateway_is_importable_from_distribution_namespace() -> None:
    from nexus_sdk.payments import NEXUSPaymentExecutionPlane

    assert NEXUSPaymentExecutionPlane is not None
