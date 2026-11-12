"""Shared helpers for the `safe2 assess --pro` tests.

Secret-shaped sentinels are assembled at runtime so no committed file contains a string
a secret scanner would flag. Every sentinel is a unique marker the manifest, bundle, notes,
and CLI output must never contain.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

FAKE_PROVIDER_KEY = "sk-" + "proj-" + "SENTINELFAKEKEY" + "0123456789abcdef"
PROMPT_SENTINEL = "SENTINEL_PROMPT_TEXT_must_not_leave_the_machine"
TOOL_ARG_SENTINEL = "SENTINEL_TOOL_ARG_must_not_leave_the_machine"
COMMAND_SENTINEL = "SENTINEL_COMMAND_LINE_must_not_leave_the_machine"
ENV_VALUE_SENTINEL = "SENTINEL_ENV_VALUE_must_not_leave_the_machine"
HEADER_SENTINEL = "SENTINEL_HEADER_VALUE_must_not_leave_the_machine"
HOME_ONLY_SENTINEL = "SENTINEL_HOME_ONLY_must_not_be_read"
PRO_KEY = "as2k_" + "SENTINELPROKEY" + "abcdef0123456789"
PINNED_HEX = "ab" * 32

LEAK_SENTINELS = (
    FAKE_PROVIDER_KEY,
    "SENTINELFAKEKEY",
    PROMPT_SENTINEL,
    TOOL_ARG_SENTINEL,
    COMMAND_SENTINEL,
    ENV_VALUE_SENTINEL,
    HEADER_SENTINEL,
    HOME_ONLY_SENTINEL,
    "SENTINELPROKEY",
)


def write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def agent_file(name: str, tools: str | None, *, extra: str = "") -> str:
    tools_line = f"tools: {tools}\n" if tools is not None else ""
    return f"---\nname: {name}\ndescription: {PROMPT_SENTINEL}\n{tools_line}{extra}---\n{PROMPT_SENTINEL}\n"


def isolate_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> Path:
    """Point every home lookup at an empty directory so the real ~/.claude is never read."""
    home.mkdir(parents=True, exist_ok=True)
    home = home.resolve()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    for name in ("SAFE2_CONFIG", "SAFE2_MCP_PRO_KEY"):
        monkeypatch.delenv(name, raising=False)
    return home


def build_golden_project(root: Path) -> None:
    """One unpinned MCP server, a spawning agent with no mandate, an unattended mail sender,
    memory without provenance, a `.env` with a fake key, and one clean control agent."""
    write(root, ".claude/agents/orchestrator.md", agent_file("orchestrator", "Task, Read, Grep"))
    write(
        root,
        ".claude/agents/mailer.md",
        agent_file("mailer", "Read, mcp__gmail__send_email", extra="permissionMode: bypassPermissions\n"),
    )
    write(
        root,
        ".claude/agents/notekeeper.md",
        agent_file("notekeeper", "Read, mcp__memory__store", extra="memory: project\n"),
    )
    write(root, ".claude/agents/reader.md", agent_file("reader", "Read, Grep"))
    # No `tools:` line: inherits the settings allow-list, which carries a tool argument.
    write(root, ".claude/agents/generalist.md", agent_file("generalist", None))
    write(
        root,
        ".mcp.json",
        json.dumps(
            {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@example/fs-server", COMMAND_SENTINEL],
                        "env": {"API_TOKEN": ENV_VALUE_SENTINEL},
                    },
                    "pinned-tool": {
                        "command": "docker",
                        "args": ["run", "-i", f"registry.example/tool@sha256:{PINNED_HEX}"],
                    },
                    "remote-docs": {
                        "type": "http",
                        "url": "https://docs.example.com/mcp",
                        "headers": {"Authorization": f"Bearer {HEADER_SENTINEL}"},
                    },
                }
            },
            indent=2,
        ),
    )
    write(
        root,
        ".claude/settings.json",
        json.dumps(
            {
                "permissions": {
                    "defaultMode": "default",
                    "allow": ["Read", f"Bash(cat {TOOL_ARG_SENTINEL}:*)"],
                    "deny": ["WebFetch"],
                    "ask": ["Edit"],
                },
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "Bash", "hooks": [{"type": "command", "command": f"echo {COMMAND_SENTINEL}"}]}
                    ]
                },
            },
            indent=2,
        ),
    )
    write(root, ".env", f"OPENAI_API_KEY={FAKE_PROVIDER_KEY}\nDEBUG=true\n")
    write(root, "README.md", "# golden\n")


def init_project(root: Path, *, max_files: int | None = None) -> None:
    limits = f"\n[limits]\nmax_files = {max_files}\nmax_file_bytes = 5000000\n" if max_files else ""
    write(
        root,
        ".safe2/config.toml",
        'schema_version = "safe2.config.v1"\n\n[project]\nprofile = "local"\nname = "golden"\n'
        "\n[privacy]\ncollect_content = false\ncollect_prompts = false\n"
        "collect_environment_values = false\nnetwork_export = false\n" + limits,
    )


def bundle_text(*paths: Path) -> str:
    """All bytes under the given files/directories, decoded leniently, for sentinel greps."""
    chunks: list[str] = []
    for path in paths:
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        chunks.extend(item.read_bytes().decode("utf-8", "replace") for item in files)
    return "\n".join(chunks)


class StubServer:
    """A loopback MCP-shaped server that records every request and returns a scripted reply."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.status = 200
        self.content_type = "application/json"
        self.body: bytes = b"{}"
        self.headers: dict[str, str] = {}
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                stub.requests.append(
                    {
                        "path": self.path,
                        "headers": {key.lower(): value for key, value in self.headers.items()},
                        "body": self.rfile.read(length),
                    }
                )
                self.send_response(stub.status)
                self.send_header("Content-Type", stub.content_type)
                for key, value in stub.headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(stub.body)))
                self.end_headers()
                self.wfile.write(stub.body)

            def log_message(self, *args: object) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}/pro/mcp"

    def __enter__(self) -> StubServer:
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()

    def reply_result(self, result: dict[str, Any]) -> None:
        self.status = 200
        self.content_type = "application/json"
        self.body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()

    def reply_success(self, structured: dict[str, Any]) -> None:
        self.reply_result(
            {"content": [{"type": "text", "text": json.dumps(structured)}], "structuredContent": structured, "isError": False}
        )

    def reply_error(self, code: str, message: str, **extra: Any) -> None:
        self.reply_result(
            {"content": [{"type": "text", "text": json.dumps({"error": {"code": code, "message": message, **extra}})}], "isError": True}
        )


SUCCESS = {
    "applied": True,
    "project_id": "proj_0123456789ab",
    "name": "golden",
    "act_tier": "ACT-4",
    "act_basis": "spawning agent",
    "manifest": {"digest": "sha256:" + "0" * 64, "source": "cli"},
    "summary": {"found": 0, "missing": 3, "uncertain": 5, "not_applicable": 1},
    "gaps": [
        {"control_id": "MCP-4", "name": "Pinned MCP servers", "state": "missing", "severity": "required", "subjects": ["mcp_server:filesystem"], "rule": "GR-01"},
        {"control_id": "CP.9", "name": "Delegation mandate", "state": "missing", "severity": "required", "subjects": ["agent:orchestrator"], "rule": "GR-02"},
    ],
    "conflicts": [],
    "snapshot_id": "snap_abc123",
    "posture_digest": "0" * 64,
    "signed": False,
}
