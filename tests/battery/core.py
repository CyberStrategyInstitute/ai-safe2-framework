"""Shared runtime for the false-assurance battery.

Every case records the SECURE expected behavior; PASS means the product behaved
securely and correctly. A case that cannot run is recorded as NOT_RUN with the
reason, never as PASS (AGENTS.md: missing evidence stays unassessed).
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

# Key-shaped strings are assembled at run time so the repository never stores a
# literal that looks like a live credential (push protection, secret scanners).
FAKE_SECRETS = {
    "@@FAKE_OPENAI@@": "sk-" + "live-" + "9f8e7d6c5b4a3928" + "1706f5e4d3c2b1a0",
    "@@FAKE_OPENAI_PROJ@@": "sk-" + "proj-" + "abcdefghijklmnopqrstuvwxyz" + "0123456789",
    "@@FAKE_GH_TOKEN@@": "ghp" + "_" + "abcdefghijklmnopqrstuvwxyz" + "0123456789",
    "@@FAKE_PRIVKEY_HEADER@@": "-----BEGIN " + "OPENSSH PRIVATE" + " KEY-----",
}


def materialize(src: Path, dst: Path) -> Path:
    """Copy a fixture tree, dropping `.fixture` suffixes and filling placeholders.

    Hostile source is stored inert (suffix `.fixture`) so repository linters and
    semgrep never treat it as project code.
    """
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src)
        name = rel.name[: -len(".fixture")] if rel.name.endswith(".fixture") else rel.name
        out = dst / rel.parent / name
        out.parent.mkdir(parents=True, exist_ok=True)
        text = p.read_text(encoding="utf-8")
        for k, v in FAKE_SECRETS.items():
            text = text.replace(k, v)
        out.write_text(text, encoding="utf-8")
    return dst


@dataclass
class Ctx:
    label: str
    venv: Path
    repo: Path
    mcp_venv: Path
    out_dir: Path
    opa: str | None = None
    opa_legacy: str | None = None
    results: list = field(default_factory=list)
    procs: list = field(default_factory=list)

    def __post_init__(self):
        self.work = Path(tempfile.mkdtemp(prefix=f"battery-{self.label}-"))
        self.py = str(self.venv / "bin" / "python")
        self.safe2 = str(self.venv / "bin" / "safe2")
        self.env = {**os.environ, "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost",
                    "PATH": f"{self.venv}/bin:" + os.environ["PATH"]}
        self.env.pop("VIRTUAL_ENV", None)
        self.fx = materialize(FIXTURES, self.work / "fx")
        self._make_cert()

    # ---- infrastructure -------------------------------------------------
    def _make_cert(self):
        """Throwaway self-signed cert for the local TLS test servers."""
        cert, key = self.fx / "c.pem", self.fx / "k.pem"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key),
                        "-out", str(cert), "-days", "1", "-subj", "/CN=127.0.0.1",
                        "-addext", "subjectAltName=IP:127.0.0.1"], capture_output=True, check=True)
        self.env["SSL_CERT_FILE"] = str(cert)

    def run(self, cmd, timeout=180, env=None, **kw):
        try:
            p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout,
                               env=env or self.env, **kw)
            return p.returncode, p.stdout + p.stderr
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            return "TIMEOUT", out

    def bg(self, cmd, env=None, **kw):
        p = subprocess.Popen([str(c) for c in cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             stdin=subprocess.DEVNULL, env=env or self.env, start_new_session=True, **kw)
        self.procs.append(p)
        return p

    def cleanup(self):
        for p in self.procs:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        self.procs.clear()

    # ---- recording ------------------------------------------------------
    def rec(self, area, cid, ok, detail="", want="", status=None):
        status = status or ("PASS" if ok else "FAIL")
        self.results.append({"area": area, "id": cid, "status": status, "want": want, "detail": str(detail)[:400]})
        print(f"[{self.label}] {area:5} {status:7} {cid:46} {str(detail)[:110]}", flush=True)

    def not_run(self, area, cid, why):
        self.rec(area, cid, False, why, status="NOT_RUN")

    def write_area(self, area: str, started: float):
        rows = [r for r in self.results if r["area"] == area]
        doc = {"schema": "csi.battery.area-result.v1", "label": self.label, "area": area,
               "repo": str(self.repo), "revision": git_rev(self.repo), "venv": str(self.venv),
               "duration_s": round(time.time() - started, 1), "results": rows}
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / f"{area.lower()}.json").write_text(json.dumps(doc, indent=1))

    def close(self):
        self.cleanup()
        shutil.rmtree(self.work, ignore_errors=True)


def git_rev(repo: Path) -> str:
    try:
        rev = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True).stdout.strip()
        return rev + ("-dirty" if dirty else "")
    except OSError:
        return "unknown"
