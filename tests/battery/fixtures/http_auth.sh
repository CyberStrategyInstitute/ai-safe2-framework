#!/bin/bash
# usage: http_auth.sh MCP_VENV SKILLS_MCP_DIR LOG_DIR PORT
# Starts the knowledge server on PORT, probes auth, stops it. Refuses to run if
# PORT already answers: a leftover server must never be measured as the one
# under test.
V=$1; D=$2; L=${3:-/tmp}; P=$4
export NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost
if [ -z "$P" ]; then echo "usage: http_auth.sh MCP_VENV SKILLS_MCP_DIR LOG_DIR PORT"; exit 2; fi
if curl -s -m 1 -o /dev/null "http://127.0.0.1:$P/"; then echo "PORT_IN_USE $P"; exit 3; fi
cd "$D/src" || exit 2
TOK="protok""1234567890""1234567"   # throwaway token for a 127.0.0.1-only test server
MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=$P TOKENS="$TOK:pro" setsid "$V/bin/python" -m mcp_server.app > "$L/http_srv_$$.log" 2>&1 < /dev/null &
PID=$!; sleep 4
H='-H Content-Type:application/json -H Accept:application/json,text/event-stream'
INIT='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}'
echo "UNAUTH $(curl -sL -m5 -o /dev/null -w '%{http_code}' -XPOST http://127.0.0.1:$P/mcp $H -d "$INIT")"
AUTHZ="Authorization: Bearer $TOK"; AUTHZ_LOWER="authorization: bearer $TOK"
echo "AUTH $(curl -sL -m5 -o /dev/null -w '%{http_code}' -XPOST http://127.0.0.1:$P/mcp $H -H "$AUTHZ" -d "$INIT")"
echo "AUTHLOWER $(curl -sL -m5 -o /dev/null -w '%{http_code}' -XPOST http://127.0.0.1:$P/mcp $H -H "$AUTHZ_LOWER" -d "$INIT")"
echo "LOG $(tail -2 "$L/http_srv_$$.log" | tr '\n' ' ' | cut -c1-200)"
kill -- -"$PID" 2>/dev/null; kill "$PID" 2>/dev/null; sleep 0.5
if curl -s -m 1 -o /dev/null "http://127.0.0.1:$P/"; then echo "WARN server still answering on $P after stop"; fi
true
