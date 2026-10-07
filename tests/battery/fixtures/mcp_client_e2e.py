"""Real MCP client against the AI SAFE2 knowledge server over stdio.
usage: mcp_client_e2e.py SKILLS_MCP_DIR CASES.jsonl
Prints `tool <name>:` per listed tool, then `### <case id> isError=<bool> len=<n>` and the body per case."""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run():
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.app"],
                                   env={**os.environ, "MCP_TRANSPORT": "stdio"}, cwd=sys.argv[1])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            init = await s.initialize()
            print("server:", init.serverInfo.name, init.serverInfo.version, "| protocol:", init.protocolVersion)
            for t in (await s.list_tools()).tools:
                print(f"tool {t.name}: required={t.inputSchema.get('required')} props={list(t.inputSchema.get('properties', {}))}")
            for line in open(sys.argv[2]):
                if not line.strip():
                    continue
                case = json.loads(line)
                try:
                    res = await s.call_tool(case["tool"], case["args"])
                    body = "\n".join(getattr(c, "text", "") for c in res.content)
                    print(f"\n### {case['id']} isError={res.isError} len={len(body)}")
                    print(body[:400000])
                except Exception as e:
                    print(f"\n### {case['id']} EXC {type(e).__name__}: {str(e)[:200]}")


asyncio.run(run())
