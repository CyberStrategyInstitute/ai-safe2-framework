"""Regression checks for source/publication/component identity drift."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "component_versions", ROOT / "scripts/check_component_versions.py"
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

INPUTS = [
    ".ai-safe2/component-versions.json",
    "ai-safe2.manifest.json",
    "pyproject.toml",
    "safe2/__init__.py",
    "safe2/safe2-docs.manifest.json",
    "safe2/README.md",
    "NEXUS/pyproject.toml",
    "NEXUS/sdk/python/nexus_sdk/__init__.py",
    "NEXUS/docker/gateway/gateway.py",
    "NEXUS/nexus-docs.manifest.json",
    "NEXUS/docker/otel/collector-config.yaml",
    "gateway/main.py",
    "gateway/provider_adapters.py",
    "examples/openclaw/gateway/gateway.py",
    "examples/openclaw/gateway/provider_adapters.py",
    "skills/mcp/pyproject.toml",
    "skills/mcp/src/mcp_server/config.py",
    "skills/ai-safe2-secure-build-copilot/SKILL.md",
    "developer-workflow/VERSION",
    "developer-workflow/MANIFEST.json",
    "developer-workflow/upstreams.lock.json",
    "developer-workflow/repository-template/.ai-safe2/workflow.json",
    "README.md",
    "AGENTS.md",
    "SECURITY.md",
    "docs/COMPONENT-VERSIONS.md",
]


@pytest.fixture
def repository(tmp_path, monkeypatch):
    for name in INPUTS:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)

    def tracked(*args, **kwargs):
        paths = [p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()]
        return SimpleNamespace(stdout="\0".join(paths).encode())

    monkeypatch.setattr(guard.subprocess, "run", tracked)
    return tmp_path


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_current_source_and_published_versions_are_distinct_and_valid(repository):
    assert guard.scan(repository) == []


@pytest.mark.parametrize(
    "text",
    [
        "[![CLI](https://img.shields.io/badge/CLI-0.8.0-orange)](x)",
        "AI SAFE² CLI 0.7.0 provides current evidence.",
        'python -m pip install "ai-safe2[all]==1.1.0"',
        'python -m pip install "ai-safe2==0.9.0"',
        'python -m pip install "nexus-a2a-sdk==0.6.0"',
        "NEXUS v0.3.0 is the current component.",
        "image: csi/nexus-gateway:0.3.0",
    ],
)
def test_stale_claims_and_unpublished_install_pins_fail(repository, text):
    write(repository, "NEXUS/docker/current.md", text)
    assert guard.scan(repository)


@pytest.mark.parametrize(
    "path,old,new",
    [
        ("safe2/__init__.py", '"1.1.0"', '"0.8.0"'),
        ("NEXUS/docker/gateway/gateway.py", '"0.6.0"', '"0.3.0"'),
        ("NEXUS/docker/otel/collector-config.yaml", '"0.6.0"', '"0.3.0"'),
        ("skills/mcp/src/mcp_server/config.py", '"3.1.0"', '"3.0.0"'),
        (
            "SECURITY.md",
            "| NEXUS reference implementation | 0.6.x |",
            "| NEXUS reference implementation | 0.5.x |",
        ),
    ],
)
def test_runtime_and_status_drift_fails(repository, path, old, new):
    source = (repository / path).read_text(encoding="utf-8")
    assert old in source
    write(repository, path, source.replace(old, new))
    assert guard.scan(repository)


def test_minimum_legacy_and_history_are_not_current_versions(repository):
    write(
        repository,
        "current.md",
        "Minimum AI SAFE2 CLI: 1.0.1\nNEXUS-A2A v0.2 protocol compatibility\nCP.5.APAY/0.4\n",
    )
    write(repository, "releases/old.md", "AI SAFE² CLI 0.8.0\nNEXUS v0.3.0\n")
    assert guard.scan(repository) == []


def test_missing_version_binding_fails_closed(repository):
    write(repository, "AGENTS.md", "# Missing component identities\n")
    assert any("missing" in error for error in guard.scan(repository))


def test_live_publication_inventory_cannot_claim_unavailable_version(repository, monkeypatch):
    class Response:
        def __enter__(self):
            import io

            return io.StringIO(json.dumps({"info": {"version": "99.0.0"}, "releases": {}}))

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(guard.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    errors = guard.scan(repository, check_pypi=True)
    assert any("99.0.0" in error for error in errors)
    assert any("no published distribution" in error for error in errors)


def test_offline_default_does_not_use_the_network(repository, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("Offline consistency checks must not access PyPI")

    monkeypatch.setattr(guard.urllib.request, "urlopen", unexpected)
    assert guard.scan(repository) == []


def test_network_failure_is_a_configuration_error(repository, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError("PyPI unavailable")

    monkeypatch.setattr(guard.urllib.request, "urlopen", unavailable)
    monkeypatch.setattr("sys.argv", ["guard", "--root", str(repository), "--check-pypi"])
    assert guard.main() == 2


def test_consistency_and_scheduled_audit_execute_the_new_guard():
    consistency = (ROOT / ".github/workflows/v31-consistency.yml").read_text()
    audit = (ROOT / ".github/workflows/release-drift.yml").read_text()
    assert "python scripts/check_component_versions.py" in consistency
    assert "paths:" not in consistency
    assert "pull_request:" in consistency and "push:" in consistency
    assert "scripts/check_component_versions.py --check-pypi" in audit
