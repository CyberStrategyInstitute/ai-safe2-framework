"""CLI releases must reach PyPI, whatever tag style the release owner uses.

Regression for 2026-10-05: the CLI 1.0.0 GitHub release was tagged
`2026-10-5_CLI_1.0.0`; publish.yml only ran for `v*` tags, so every job was
skipped, PyPI stayed on 0.9.0 and the README install command failed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_pypi_release import audit, wait_for  # noqa: E402
from check_release_installation import check_tag, cli_version_from_tag  # noqa: E402

WORKFLOWS = ROOT / ".github" / "workflows"


@pytest.mark.parametrize("tag,version", [
    ("v1.0.1", "1.0.1"),
    ("v1.1.0rc1", "1.1.0rc1"),
    ("2026-10-5_CLI_1.0.0", "1.0.0"),
    ("2026-10-12_CLI_1.0.1", "1.0.1"),
    ("2026_09_20_CLI_0.7.0", "0.7.0"),
    ("2026-09-17_CLI_0.6.0_Scope_Attribute_Decide", "0.6.0"),
    ("2026-09-09_safe2_CLI_0.2.0", "0.2.0"),
    ("2026-10-12_cli_v1.0.1", "1.0.1"),
    ("v3.1", None),                         # framework tag
    ("nexus-v0.5.0", None),                 # NEXUS has its own workflow
    ("2026-10-02_AISM_Scoring_Update", None),
    ("2026-05-09_safe2_CLI_Update", None),  # CLI release that names no version
    ("2026-10-12_CLI_1.0.1.2", None),
])
def test_cli_version_from_tag(tag, version):
    assert cli_version_from_tag(tag) == version


def test_check_tag_accepts_both_styles_when_version_matches():
    check_tag("v1.0.1", "1.0.1")
    check_tag("2026-10-12_CLI_1.0.1", "1.0.1")


@pytest.mark.parametrize("tag", ["2026-10-12_CLI_1.0.0", "v1.0.0", "2026-05-09_safe2_CLI_Update", "v3.1"])
def test_check_tag_fails_closed_on_mismatch_or_missing_version(tag):
    with pytest.raises(RuntimeError):
        check_tag(tag, "1.0.1")


def _rel(tag, at, prerelease=False, draft=False):
    return {"tag_name": tag, "published_at": at, "prerelease": prerelease, "draft": draft}


def test_audit_fails_when_newest_cli_release_is_not_on_pypi():
    releases = [_rel("2026-10-5_CLI_1.0.0", "2026-10-05T14:07:38Z"),
                _rel("nexus-v0.5.0", "2026-10-04T23:43:38Z"),
                _rel("2026-09-27_CLI_0.9.0", "2026-09-27T20:37:22Z")]
    failures, _ = audit(releases, {"0.9.0"})
    assert len(failures) == 1 and "1.0.0" in failures[0]


def test_audit_passes_when_newest_is_published_and_warns_on_older_gaps():
    releases = [_rel("v1.0.1", "2026-10-12T00:00:00Z"), _rel("2026-10-5_CLI_1.0.0", "2026-10-05T14:07:38Z")]
    failures, warnings = audit(releases, {"0.9.0", "1.0.1"})
    assert failures == [] and any("1.0.0" in w for w in warnings)


def test_audit_ignores_prereleases_and_drafts():
    releases = [_rel("v1.1.0rc1", "2026-11-01T00:00:00Z", prerelease=True),
                _rel("v1.2.0", "2026-11-02T00:00:00Z", draft=True),
                _rel("v1.0.1", "2026-10-12T00:00:00Z")]
    assert audit(releases, {"1.0.1"})[0] == []


def test_wait_for_succeeds_once_pypi_lists_the_version_and_times_out_otherwise():
    calls = iter([set(), {"0.9.0"}, {"0.9.0", "1.0.1"}])
    assert wait_for("1.0.1", lambda: next(calls), timeout_s=60, interval_s=0, sleep=lambda _: None)
    assert not wait_for("1.0.1", lambda: {"0.9.0"}, timeout_s=0, interval_s=0, sleep=lambda _: None)


def test_publish_workflow_runs_for_dated_cli_tags_and_verifies_upload():
    wf = yaml.safe_load((WORKFLOWS / "publish.yml").read_text(encoding="utf-8"))
    jobs = wf["jobs"]
    assert "contains(github.event.release.tag_name, 'CLI')" in jobs["build"]["if"]
    assert jobs["build"]["outputs"]["version"]
    # The OIDC publishing token is scoped to the publish jobs, not the build that runs tests.
    assert "id-token" not in wf.get("permissions", {})
    for name in ("publish-pypi", "publish-testpypi"):
        assert jobs[name]["permissions"]["id-token"] == "write"
        assert "startsWith" not in jobs[name]["if"]
    verify = jobs["verify-pypi"]
    assert set(verify["needs"]) == {"build", "publish-pypi"}
    assert "id-token" not in verify["permissions"]
    steps = " ".join(s.get("run", "") for s in verify["steps"])
    assert "check_pypi_release.py wait" in steps and "safe2 --version" in steps


def test_drift_audit_runs_weekly():
    wf = yaml.safe_load((WORKFLOWS / "release-drift.yml").read_text(encoding="utf-8"))
    triggers = wf.get("on") or wf.get(True)
    assert triggers["schedule"] and "workflow_dispatch" in triggers
    assert wf["permissions"] == {"contents": "read"}
    assert "check_pypi_release.py audit" in " ".join(s.get("run", "") for s in wf["jobs"]["audit"]["steps"])
