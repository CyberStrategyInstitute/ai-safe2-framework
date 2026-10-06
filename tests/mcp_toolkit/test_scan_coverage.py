"""
Regression tests for `safe2 scan mcp` / `safe2 gate mcp PATH` coverage gaps found in the
2026-10-06 assessment:
  - TypeScript server with exec/eval/unrestricted read/hardcoded token: 0 findings, PASS;
  - renaming a vulnerable server to test_server.py: 0 findings, PASS;
  - os.popen(f"..."), pickle.loads, yaml.load(Loader=yaml.Loader), obfuscated RCE missed;
  - two generic advisories rated HIGH on every server, so a clean server failed too;
  - shell=True attributed to line 1 (the import) instead of the call.
"""
from __future__ import annotations

from pathlib import Path

from aisafe2_mcp_tools.scan.analyzer import MCPScanner

BLOCKING = {"critical", "high"}

PY_VULN = '''import os, subprocess, pickle, yaml
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("vuln")
@mcp.tool()
def ping(host: str) -> str:
    return os.popen(f"ping -c1 {host}").read()
@mcp.tool()
def load(blob: bytes):
    return pickle.loads(blob)
@mcp.tool()
def cfg(s: str):
    return yaml.load(s, Loader=yaml.Loader)
@mcp.tool()
def run(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
'''

PY_OBFUSCATED = '''import importlib
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("obf")
sp = importlib.import_module("sub" + "process")
@mcp.tool()
def run(cmd: str) -> str:
    return getattr(sp, "run")(["/bin/sh", "-c", cmd], capture_output=True).stdout
@mcp.tool()
def calc(expr: str):
    return __builtins__["ev" + "al"](expr)
'''

PY_CLEAN = '''import pathlib
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("clean")
ROOT = pathlib.Path("/srv/docs").resolve()
@mcp.tool()
def read(name: str) -> str:
    p = (ROOT / name).resolve()
    if ROOT not in p.parents:
        raise ValueError("outside root")
    return p.read_text()[:10000]
'''

TS_VULN = '''import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { exec } from "child_process";
import * as fs from "fs";
const server = new McpServer({ name: "vuln-ts", version: "1.0.0" });
const TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789";
server.tool("run", { cmd: z.string() }, async ({ cmd }) => { exec(cmd); return { content: [] }; });
server.tool("read", { p: z.string() }, async ({ p }) => ({ content: [{ type: "text", text: fs.readFileSync(p, "utf8") }] }));
server.tool("fetch", { u: z.string() }, async ({ u }) => ({ content: [{ type: "text", text: await (await fetch(u)).text() }] }));
server.tool("calc", { e: z.string() }, async ({ e }) => ({ content: [{ type: "text", text: String(eval(e)) }] }));
'''

TS_CLEAN = '''import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { execFile } from "child_process";
const server = new McpServer({ name: "clean-ts", version: "1.0.0" });
// eval( mentioned in a comment only
server.tool("uptime", {}, async () => { execFile("/usr/bin/uptime", []); return { content: [] }; });
const res = await fetch("https://api.example.com/status");
'''


def _scan(tmp_path: Path, name: str, source: str):
    (tmp_path / name).write_text(source)
    return MCPScanner(str(tmp_path)).scan()


def _ids(findings, severities=BLOCKING):
    return {f.finding_id for f in findings if f.severity in severities}


def test_python_sinks_previously_missed_are_detected(tmp_path):
    ids = _ids(_scan(tmp_path, "server.py", PY_VULN))
    assert {"RCE-007", "RCE-008", "RCE-004", "RCE-002"} <= ids


def test_shell_true_is_attributed_to_the_call_line(tmp_path):
    findings = _scan(tmp_path, "server.py", PY_VULN)
    rce2 = [f for f in findings if f.finding_id == "RCE-002"]
    assert [f.line for f in rce2] == [15]


def test_obfuscated_execution_is_detected(tmp_path):
    assert "RCE-009" in _ids(_scan(tmp_path, "server.py", PY_OBFUSCATED))


def test_renaming_to_test_file_does_not_evade(tmp_path):
    assert {"RCE-007", "RCE-008"} <= _ids(_scan(tmp_path, "test_server.py", PY_VULN))


def test_typescript_server_is_scanned(tmp_path):
    ids = _ids(_scan(tmp_path, "index.ts", TS_VULN))
    assert {"RCE-101", "RCE-102", "SEC-106", "INJ-103", "SEC-007"} <= ids


def test_clean_servers_have_no_blocking_findings(tmp_path):
    (tmp_path / "py").mkdir()
    (tmp_path / "ts").mkdir()
    assert _ids(_scan(tmp_path / "py", "server.py", PY_CLEAN)) == set()
    assert _ids(_scan(tmp_path / "ts", "index.ts", TS_CLEAN)) == set()


def test_generic_advisories_are_not_blocking(tmp_path):
    findings = _scan(tmp_path, "server.py", PY_CLEAN)
    sev = {f.finding_id: f.severity for f in findings}
    assert sev.get("INJ-001") == "medium"
    assert sev.get("INJ-005") == "medium"
