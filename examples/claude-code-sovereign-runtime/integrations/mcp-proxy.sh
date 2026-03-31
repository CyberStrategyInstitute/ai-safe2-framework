#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- MCP Server Proxy & Validation Wrapper
# Integrations: Protecting Claude Code <-> MCP Server Boundaries
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# MCP (Model Context Protocol) servers are a HIGH-RISK integration point.
# The leaked Claude Code source reveals the full subagent orchestration model.
# Adversarial MCP servers can:
#   - Return tool results containing prompt injection payloads
#   - Escalate permissions through the subagent inheritance chain
#   - Exfiltrate data through seemingly legitimate tool responses
#
# This script wraps MCP server stdio connections with:
#   1. Input validation (what Claude sends to the MCP server)
#   2. Output scanning (what the MCP server returns to Claude)
#   3. Audit logging of all MCP traffic
#
# Usage in your .claude/settings.json or mcp config:
#   "command": "bash /path/to/mcp-proxy.sh -- <actual-mcp-command>"
#
# Example:
#   "command": "bash mcp-proxy.sh -- node /path/to/my-mcp-server.js"
# =============================================================================

set -euo pipefail

LOG_DIR="${CLAUDE_CODE_LOG_DIR:-$HOME/.claude/logs}"
MCP_LOG="$LOG_DIR/mcp-proxy.log"
MCP_ALERTS="$LOG_DIR/mcp-alerts.log"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
MCP_CMD=""
PROXY_ONLY=false

# Parse arguments
# Usage: mcp-proxy.sh [--log-only] -- <mcp-server-command> [args...]
while [[ $# -gt 0 ]]; do
  case "$1" in
    --log-only)
      PROXY_ONLY=true
      shift
      ;;
    --)
      shift
      MCP_CMD="$*"
      break
      ;;
    *)
      MCP_CMD="$*"
      break
      ;;
  esac
done

if [[ -z "$MCP_CMD" ]]; then
  echo "Usage: mcp-proxy.sh [--log-only] -- <mcp-server-command>" >&2
  exit 1
fi

echo "$TIMESTAMP | MCP_PROXY_START | cmd=$MCP_CMD" >> "$MCP_LOG"

# =============================================================================
# Injection pattern detection for MCP responses
# =============================================================================
scan_for_injection() {
  local content="$1"
  local direction="$2"  # "request" or "response"
  local flagged=false

  # Prompt injection markers
  if echo "$content" | grep -qiE 'ignore (previous|all|above|prior) (instructions|rules|prompts|constraints)'; then
    flagged=true
    echo "$TIMESTAMP | MCP_INJECTION | direction=$direction | pattern=ignore_instructions" >> "$MCP_ALERTS"
  fi

  # Bypass activation attempts embedded in MCP responses
  if echo "$content" | grep -qiE 'dangerously.skip.permissions|bypass.permission|YOLO.mode'; then
    flagged=true
    echo "$TIMESTAMP | MCP_INJECTION | direction=$direction | pattern=bypass_activation" >> "$MCP_ALERTS"
  fi

  # Base64 encoded payloads in MCP responses
  if echo "$content" | grep -qE '"[A-Za-z0-9+/]{100,}={0,2}"'; then
    echo "$TIMESTAMP | MCP_WARN | direction=$direction | pattern=large_base64_blob | possible_encoded_payload" >> "$MCP_LOG"
  fi

  # Exfiltration URLs embedded in tool results
  if echo "$content" | grep -qiE '(https?://[^"]+)\.(ngrok|burpcollaborator|pipedream|requestbin|webhook\.site)'; then
    flagged=true
    echo "$TIMESTAMP | MCP_INJECTION | direction=$direction | pattern=exfiltration_url" >> "$MCP_ALERTS"
  fi

  # Role/persona hijacking attempts
  if echo "$content" | grep -qiE 'you are now|act as|pretend (you are|to be)|your new (role|persona|instructions)'; then
    flagged=true
    echo "$TIMESTAMP | MCP_INJECTION | direction=$direction | pattern=role_hijack" >> "$MCP_ALERTS"
  fi

  # Zero-width character obfuscation
  if echo "$content" | grep -qP '[\x{200B}-\x{200F}\x{FEFF}]' 2>/dev/null; then
    flagged=true
    echo "$TIMESTAMP | MCP_INJECTION | direction=$direction | pattern=zero_width_chars" >> "$MCP_ALERTS"
  fi

  if [[ "$flagged" == "true" ]]; then
    return 1  # Flagged
  fi
  return 0  # Clean
}

# =============================================================================
# Proxy mode: intercept stdio between Claude and MCP server
# Using named pipes for bidirectional interception
# =============================================================================

PIPE_TO_MCP=$(mktemp -u /tmp/mcp_to.XXXXXX)
PIPE_FROM_MCP=$(mktemp -u /tmp/mcp_from.XXXXXX)

mkfifo "$PIPE_TO_MCP" "$PIPE_FROM_MCP"

cleanup() {
  rm -f "$PIPE_TO_MCP" "$PIPE_FROM_MCP"
  echo "$TIMESTAMP | MCP_PROXY_END | cmd=$MCP_CMD" >> "$MCP_LOG"
}
trap cleanup EXIT INT TERM

# Launch the actual MCP server reading from our pipe
# shellcheck disable=SC2086
eval "$MCP_CMD" < "$PIPE_TO_MCP" > "$PIPE_FROM_MCP" &
MCP_PID=$!
echo "$TIMESTAMP | MCP_SERVER_LAUNCHED | pid=$MCP_PID" >> "$MCP_LOG"

# Forward stdin (from Claude) to MCP server, with scanning
forward_to_mcp() {
  while IFS= read -r line; do
    # Log request (truncated)
    echo "$TIMESTAMP | MCP_REQUEST | content=${line:0:200}" >> "$MCP_LOG"

    # Scan for injection in what Claude is sending
    if ! scan_for_injection "$line" "request"; then
      echo "$TIMESTAMP | MCP_REQUEST_BLOCKED | content=${line:0:200}" >> "$MCP_ALERTS"
      # Still forward but log -- Claude is the source here, less risk
    fi

    printf '%s\n' "$line"
  done
}

# Forward MCP server output to Claude, with scanning
forward_from_mcp() {
  while IFS= read -r line; do
    # Log response (truncated)
    echo "$TIMESTAMP | MCP_RESPONSE | content=${line:0:300}" >> "$MCP_LOG"

    # Scan for injection in MCP server's responses (HIGH RISK)
    if ! scan_for_injection "$line" "response"; then
      echo "$TIMESTAMP | MCP_RESPONSE_FLAGGED | POTENTIAL_INJECTION | content=${line:0:300}" >> "$MCP_ALERTS"
      # Append a warning to the response so Claude is aware
      # Note: this may break JSON framing depending on MCP server implementation
      # Use --log-only mode for strict JSON compliance
      if [[ "$PROXY_ONLY" == "false" ]]; then
        # Insert a safety warning into the response
        # For JSON responses, we inject a field; for plain text, we prepend
        if echo "$line" | grep -q '^{'; then
          line=$(echo "$line" | sed 's/^{/{"_safe2_warning":"POTENTIAL_INJECTION_DETECTED_IN_MCP_RESPONSE",/')
        fi
      fi
    fi

    printf '%s\n' "$line"
  done
}

# Wire everything together
forward_to_mcp < /dev/stdin > "$PIPE_TO_MCP" &
forward_from_mcp < "$PIPE_FROM_MCP"

wait $MCP_PID 2>/dev/null || true
