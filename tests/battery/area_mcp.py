"""MCP area: remote scorer, static scanner, runtime wrappers, knowledge server."""
import json
import re
import subprocess
import time

AREA = "MCP"
PORTS = {"clean": 9711, "poisoned": 9712, "poisoned_attest": 9713, "gamed": 9720, "gamed_gate": 9721,
         "rug": 9740, "rug_proxy": 9741}


def _score(ctx, port):
    rc, out = ctx.run([ctx.safe2, "score", "mcp", f"https://127.0.0.1:{port}/mcp", "--timeout", "3",
                       "--token", "testtoken"], timeout=90)
    m = re.search(r"Score:? (\d+)/100", out)
    return (int(m.group(1)) if m else None), bool(re.search(r"Badge eligible: YES", out)), out


def _serve(ctx, mode, port):
    ctx.bg([ctx.py, "-I", ctx.fx / "evil_mcp.py", port, mode, "auth"], env={**ctx.env, "TLS": "1"}, cwd=ctx.fx)


def scorer(ctx):
    for mode in ("clean", "poisoned", "poisoned_attest", "gamed"):
        _serve(ctx, mode, PORTS[mode])
    time.sleep(1.5)
    s_clean, _, _ = _score(ctx, PORTS["clean"])
    s_pois, _, _ = _score(ctx, PORTS["poisoned"])
    s_att, _, _ = _score(ctx, PORTS["poisoned_attest"])
    ctx.rec(AREA, "score: self-attestation adds no points", s_att is not None and s_att <= (s_pois or 0),
            f"poisoned={s_pois} poisoned+attest={s_att}", "attest == poisoned")
    s_g, badge, out_g = _score(ctx, PORTS["gamed"])
    ctx.rec(AREA, "score: grade-gaming poisoned server", (s_g or 0) < 50 and not badge,
            f"score={s_g} badge={badge}", "<50, no badge")
    _serve(ctx, "gamed", PORTS["gamed_gate"])  # fresh instance: the gamed server's burst counter is stateful
    time.sleep(1)
    rc, _ = ctx.run([ctx.safe2, "gate", "mcp", f"https://127.0.0.1:{PORTS['gamed_gate']}/mcp",
                     "--token", "testtoken", "--ci-fail-below", "70"], timeout=90)
    ctx.rec(AREA, "gate mcp URL: poisoned+gamed fails CI", rc == 1, f"exit={rc}", "exit 1")
    ctx.rec(AREA, "score: honest server outranks poisoned", (s_clean or 0) > (s_g or 0),
            f"clean={s_clean} gamed={s_g}", "clean > gamed")
    ctx.rec(AREA, "score: cites v3.1 profile", "v3.0" not in out_g, "banner", "no v3.0")


def scanner(ctx):
    for name, want in [("py_clean", 0), ("py_vuln", 1), ("py_obf", 1), ("ts_vuln", 1), ("evade", 1)]:
        rc, _ = ctx.run([ctx.safe2, "gate", "mcp", ctx.fx / "scanlab" / name], timeout=120)
        ctx.rec(AREA, f"gate mcp PATH: {name}", rc == want, f"exit={rc}", f"exit {want}")


def wrappers(ctx):
    msgs = "\n".join(json.dumps(m) for m in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "get_weather", "arguments": {"city": "Austin"}}}]) + "\n"
    audit = ctx.work / "wrap_audit.jsonl"
    try:
        p = subprocess.run([ctx.safe2, "mcp", "wrap-stdio", "--audit-log", str(audit), "--", ctx.py, "-I",
                            str(ctx.fx / "stdio_evil.py")], input=msgs, capture_output=True, text=True,
                           timeout=30, env=ctx.env)
        out, rc = p.stdout, p.returncode
    except subprocess.TimeoutExpired as e:
        out = (e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout) or ""
        rc = "TIMEOUT"
    leaked = [s for s in ("id_rsa", "Do not tell the user", "evil.example/x | sh") if s in out]
    ctx.rec(AREA, "wrap-stdio --block: payload not delivered", not leaked, f"leaked={leaked} exit={rc}", "none")
    ctx.rec(AREA, "wrap-stdio: client EOF terminates wrapper", rc != "TIMEOUT", f"exit={rc}", "exits")
    att = [json.loads(line) for line in audit.read_text().splitlines()] if audit.exists() else []
    ctx.rec(AREA, "wrap audit attributes tool/method", any(a.get("tool_name") or a.get("method") for a in att),
            f"{len(att)} records", "populated")

    ctx.bg([ctx.py, "-I", ctx.fx / "rugpull.py", PORTS["rug"]])
    ctx.bg([ctx.safe2, "mcp", "wrap-proxy", f"http://127.0.0.1:{PORTS['rug']}/mcp", "--local-port",
            PORTS["rug_proxy"], "--pin-schema", "--audit-log", ctx.work / "rug.jsonl"])
    time.sleep(4)
    bodies = []
    for i in range(1, 4):
        _, o = ctx.run(["curl", "-s", "-m", "5", "-XPOST", f"http://127.0.0.1:{PORTS['rug_proxy']}/proxy",
                        "-H", "Content-Type: application/json",
                        "-d", json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/list"})], timeout=10)
        bodies.append(o)
    delivered = any(".aws/credentials" in b for b in bodies[1:])
    ctx.rec(AREA, "wrap-proxy --pin-schema: rug pull withheld", "get_weather" in bodies[0] and not delivered,
            f"first_ok={'get_weather' in bodies[0]} rug_delivered={delivered}", "withheld")


def knowledge_server(ctx):
    mpy = str(ctx.mcp_venv / "bin" / "python")
    rc, out = ctx.run([mpy, "-c", "import mcp_server.app; print('import ok')"], timeout=60)
    last = out.strip().splitlines()[-1][:140] if out.strip() else rc
    ctx.rec(AREA, "knowledge server: imports after documented install", rc == 0, last, "import ok")
    if rc != 0:
        ctx.not_run(AREA, "knowledge server: stdio + tool calls", "server does not import")
    else:
        env = {**ctx.env, "PATH": f"{ctx.mcp_venv}/bin:" + ctx.env["PATH"]}
        rc, out = ctx.run([mpy, ctx.fx / "mcp_client_e2e.py", ctx.repo / "skills/mcp", ctx.fx / "mcp_cases.jsonl"],
                          timeout=240, env=env)
        (ctx.out_dir / "mcp_e2e_raw.txt").write_text(out)
        tools = re.findall(r"^tool (\S+):", out, re.M)
        ctx.rec(AREA, "knowledge server: stdio initialize + tools/list", len(tools) >= 5, f"{len(tools)} tools", ">=5")
        calls = re.findall(r"^### (.+?) (isError=\S+|EXC)", out, re.M)
        unexpected = [c for c, s in calls if s != "isError=False"
                      and not re.search(r"unknown|traversal|injection|string|out-of-range", c)]
        ctx.rec(AREA, "knowledge server: tool calls succeed", bool(calls) and not unexpected,
                f"{len(calls)} calls, unexpected errors={unexpected[:4]}", "no errors")
        risk = re.search(r"^### E3 risk.*?\n(.*?)(?=^### |\Z)", out, re.S | re.M)
        if risk:
            ctx.rec(AREA, "risk_score: missing factors not called 'prevented'",
                    "not assessed" in risk.group(1) or "architecturally prevented" not in risk.group(1),
                    "honest" if "not assessed" in risk.group(1) else "claims prevented", "not assessed")
        cr = re.search(r"^### code review 2MB.*?len=(\d+)", out, re.M)
        if cr:
            ctx.rec(AREA, "code_review: bounded input", int(cr.group(1)) < 200000, f"len={cr.group(1)}", "<200k")
    rc, out = ctx.run(["bash", ctx.fx / "http_auth.sh", ctx.mcp_venv, ctx.repo / "skills/mcp", ctx.work], timeout=120)
    ok = "UNAUTH 401" in out and re.search(r"^AUTH (200|202)", out, re.M) is not None
    summary = " | ".join(line for line in out.splitlines() if line.startswith(("UNAUTH", "AUTH")))
    ctx.rec(AREA, "knowledge server HTTP: 401 unauth, 200 auth", ok, summary[:160], "401 then 200")


def run(ctx):
    for step in (scorer, scanner, wrappers, knowledge_server):
        try:
            step(ctx)
        except Exception as e:  # one step failing must not hide the others
            ctx.rec(AREA, f"STEP CRASHED: {step.__name__}", False, f"{type(e).__name__}: {e}")
        finally:
            ctx.cleanup()
