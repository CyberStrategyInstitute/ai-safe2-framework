"""
Every CP.5.MCP control the scanner *prints* must be the control it *emits*.

Found in the 2026-10-07 repository consistency sweep: the finding-to-control map
(`Finding.control_for`) was migrated to the v3.1 MCP-1..MCP-19 profile, but the
human-readable text was not. Users were told, for example, that a 0.0.0.0 bind
violates "MCP-6" while the JSON said MCP-3, that MCP-12 is "Swarm C2 Detection"
(v3.1 MCP-12 is Principal-Scoped State), and that MCP-9 is "Context-Tool
Isolation" (v3.1 MCP-9 is Secret Boundary). The dependency checker also emitted
MCP-3 for DEP findings while the map says MCP-4.

These tests bind the prose, the fix templates and the emitted findings to one
source of truth, and bind any `MCP-N (Name)` citation to the canonical v3.1 name.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from aisafe2_mcp_tools.scan import pattern_scanner as ps
from aisafe2_mcp_tools.scan.analyzer import MCPScanner
from aisafe2_mcp_tools.scan.findings import VALID_FINDING_IDS, Finding

ROOT = Path(__file__).resolve().parents[2]
TOOLKIT = ROOT / "aisafe2_mcp_tools"
FIXES = TOOLKIT / "scan" / "fixes"
PROFILE = ROOT / "skills" / "mcp" / "data" / "mcp-profile-v3.1.json"

# "MCP-UPD" is a threat name (parasitic toolchain attack), not a control.
CITED = re.compile(r"\bMCP-(\d{1,2})\b")
NAMED = re.compile(r"\bMCP-(\d{1,2})\s*\((?![^)]*\d{3})([A-Z][A-Za-z0-9–\- ]{3,60})\)")


def _canonical_names() -> dict[str, str]:
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    return {c["id"]: c["name"] for c in data["controls"]}


def _norm(name: str) -> str:
    name = name.replace("–", "-").lower()
    name = re.sub(r"\bcontrols?\b", "", name)
    return re.sub(r"[^a-z]+", " ", name).strip()


def _pattern_rows():
    for table in (ps.CRITICAL_PATTERNS, ps.HIGH_PATTERNS, ps.MEDIUM_PATTERNS, ps.LOW_PATTERNS):
        for row in table:
            finding_id, _pattern, title, desc, _cves, remediation = row[:6]
            yield finding_id, " ".join((title, desc, remediation))
    for finding_id, _sev, _pattern, title, desc, remediation in ps.JS_PATTERNS:
        yield finding_id, " ".join((title, desc, remediation))


_ROWS = list(_pattern_rows())


@pytest.mark.parametrize("finding_id,text", _ROWS, ids=[r[0] for r in _ROWS])
def test_pattern_text_cites_the_emitted_control(finding_id, text):
    cited = {f"MCP-{n}" for n in CITED.findall(text)}
    expected = Finding.control_for(finding_id)
    assert cited <= {expected}, (
        f"{finding_id} text cites {sorted(cited)} but the finding is emitted as {expected}"
    )


def test_cti001_text_cites_the_emitted_control():
    lines = ["data = get_file(p)", "send_email(to, data)"]
    findings = list(ps.PatternScanner()._check_cti001("\n".join(lines), "s.py", lines))
    assert findings, "CTI-001 fixture did not fire"
    for f in findings:
        cited = {f"MCP-{n}" for n in CITED.findall(f.description + " " + f.remediation)}
        assert cited <= {f.cp5_control}, f"CTI-001 cites {sorted(cited)}, emitted {f.cp5_control}"


@pytest.mark.parametrize("template", sorted(FIXES.glob("*.template")), ids=lambda p: p.stem)
def test_fix_template_cites_the_emitted_control(template):
    finding_id = template.stem
    assert finding_id in VALID_FINDING_IDS
    cited = {f"MCP-{n}" for n in CITED.findall(template.read_text(encoding="utf-8"))}
    expected = Finding.control_for(finding_id)
    assert cited <= {expected}, f"{template.name} cites {sorted(cited)}, finding emits {expected}"


def test_every_emitted_finding_uses_the_control_map(tmp_path):
    (tmp_path / "server.py").write_text(
        "import subprocess, os\n"
        "from mcp.server.fastmcp import FastMCP\n"
        "from mcp import StdioServerParameters\n"
        "mcp = FastMCP('x')\n"
        "params = StdioServerParameters(command=os.environ['CMD'])\n"
        "@mcp.tool()\n"
        "def run(c: str):\n"
        "    return subprocess.run(c, shell=True)\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text("mcp\nlitellm==1.0.0\n", encoding="utf-8")
    findings = MCPScanner(str(tmp_path)).scan()
    ids = {f.finding_id for f in findings}
    assert {"RCE-001", "DEP-001", "DEP-002"} <= ids, ids
    wrong = {(f.finding_id, f.cp5_control) for f in findings
             if f.cp5_control != Finding.control_for(f.finding_id)}
    assert not wrong, f"findings emitted with a control other than the map: {sorted(wrong)}"


def test_named_citations_use_v31_control_names():
    canonical = _canonical_names()
    bad = []
    for path in sorted(TOOLKIT.rglob("*")):
        if path.suffix not in {".py", ".template", ".md", ".html"} or "__pycache__" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for num, name in NAMED.findall(line):
                want = canonical.get(f"MCP-{num}")
                if want is None or not _norm(want).startswith(_norm(name)) and _norm(name) not in _norm(want):
                    bad.append(f"{path.relative_to(ROOT)}:{lineno}: MCP-{num} ({name}) != {want}")
    assert not bad, "\n".join(bad)


SCORE = TOOLKIT / "score"
CHECK_CTOR = re.compile(r'check_id="([A-Z]+)",\s*name="[^"]*",\s*cp5_control="(MCP-\d+)"')


def _emitted_check_controls() -> dict[str, set[str]]:
    emitted: dict[str, set[str]] = {}
    for path in SCORE.glob("*.py"):
        for check_id, control in CHECK_CTOR.findall(path.read_text(encoding="utf-8")):
            emitted.setdefault(check_id, set()).add(control)
    return emitted


def test_each_remote_check_emits_one_control():
    emitted = _emitted_check_controls()
    assert {"AUTH", "TLS", "INJECTION", "FSP", "HEADERS", "RATE", "SESSION", "SSRF"} <= set(emitted)
    split = {k: sorted(v) for k, v in emitted.items() if len(v) != 1}
    assert not split, f"check emitted under more than one control: {split}"


def test_remote_check_remediation_cites_the_emitted_control():
    from aisafe2_mcp_tools.score import assessor, auth_checker, header_checker, schema_scanner, ssrf_detector

    emitted = {k: next(iter(v)) for k, v in _emitted_check_controls().items()}
    texts = dict(assessor._REMEDIATIONS)
    texts.update({
        "AUTH#auth_checker": auth_checker._REMEDIATION,
        "HEADERS#header_checker": header_checker._REMEDIATION,
        "SSRF#ssrf_detector": ssrf_detector._REMEDIATION,
    })
    texts["INJECTION#schema_scanner"] = schema_scanner._INJ_REMEDIATION
    texts["FSP#schema_scanner"] = schema_scanner._FSP_REMEDIATION
    wrong = {}
    for key, text in texts.items():
        check_id = key.split("#")[0]
        cited = {f"MCP-{n}" for n in CITED.findall(text)}
        if not cited <= {emitted[check_id]}:
            wrong[key] = (sorted(cited), emitted[check_id])
    assert not wrong, f"remediation cites a control the check does not emit: {wrong}"
