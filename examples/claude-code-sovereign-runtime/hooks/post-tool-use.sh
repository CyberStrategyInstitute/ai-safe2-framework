#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Post-Tool-Use Hook
# Sovereign Runtime Governor: Output Monitoring & Secret Leak Detection
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# This hook runs AFTER every Claude Code tool execution.
# It cannot block (that is PreToolUse's job).
# It logs results, scans for leaked secrets, and triggers alerts.
#
# Claude Code passes tool result as JSON via stdin:
# {"tool_name": "...", "tool_input": {...}, "tool_result": {...}, ...}
# =============================================================================

set -euo pipefail

LOG_DIR="${CLAUDE_CODE_LOG_DIR:-$HOME/.claude/logs}"
LOG_FILE="$LOG_DIR/post-tool-use.log"
ALERT_FILE="$LOG_DIR/security-alerts.log"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Read stdin
INPUT=$(cat)

# Extract fields
if command -v jq &>/dev/null; then
  TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null || echo "unknown")
  TOOL_RESULT=$(echo "$INPUT" | jq -r '.tool_result // ""' 2>/dev/null || echo "")
  BASH_CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
else
  TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)".*/\1/' || echo "unknown")
  TOOL_RESULT=$(echo "$INPUT" | grep -o '"tool_result"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 || echo "")
  BASH_CMD=""
fi

# Truncate for logging (do not log full output -- may contain secrets)
# Log tool completion
echo "$TIMESTAMP | COMPLETED | tool=$TOOL_NAME | cmd=${BASH_CMD:0:200}" >> "$LOG_FILE"

# =============================================================================
# Secret pattern detection in tool output
# This catches cases where Claude Code read a file containing secrets
# or a command output leaked credentials
# =============================================================================

SECRET_FOUND=false
SECRET_TYPE=""

check_secret() {
  local pattern="$1"
  local label="$2"
  local content="$3"
  if echo "$content" | grep -qiE "$pattern" 2>/dev/null; then
    SECRET_FOUND=true
    SECRET_TYPE="$label"
    return 0
  fi
  return 1
}

# Only scan bash and file-read results (highest risk)
if [[ "$TOOL_NAME" == "Bash" ]] || [[ "$TOOL_NAME" == "Read" ]]; then

  check_secret 'AKIA[0-9A-Z]{16}' "AWS Access Key ID" "$TOOL_RESULT" || true
  check_secret '[0-9a-zA-Z/+]{40}' "Possible AWS Secret Key" "$TOOL_RESULT" || true
  check_secret 'sk-ant-[a-zA-Z0-9\-_]{90,}' "Anthropic API Key" "$TOOL_RESULT" || true
  check_secret 'sk-[a-zA-Z0-9]{48,}' "OpenAI API Key" "$TOOL_RESULT" || true
  check_secret 'ghp_[a-zA-Z0-9]{36,}' "GitHub Personal Access Token" "$TOOL_RESULT" || true
  check_secret 'ghs_[a-zA-Z0-9]{36,}' "GitHub App Token" "$TOOL_RESULT" || true
  check_secret 'xox[baprs]-[0-9a-zA-Z\-]{10,}' "Slack Token" "$TOOL_RESULT" || true
  check_secret 'eyJ[a-zA-Z0-9\-_]{30,}\.[a-zA-Z0-9\-_]{30,}\.[a-zA-Z0-9\-_]{30,}' "JWT Token" "$TOOL_RESULT" || true
  check_secret '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' "Private Key" "$TOOL_RESULT" || true
  check_secret 'password[[:space:]]*=[[:space:]]*["\047][^"\047]{8,}' "Password in config" "$TOOL_RESULT" || true
  check_secret 'api[_-]?key[[:space:]]*=[[:space:]]*["\047][^"\047]{16,}' "API Key in config" "$TOOL_RESULT" || true

  if [[ "$SECRET_FOUND" == "true" ]]; then
    ALERT_MSG="$TIMESTAMP | SECRET_DETECTED | type=$SECRET_TYPE | tool=$TOOL_NAME | cmd=${BASH_CMD:0:200}"
    echo "$ALERT_MSG" >> "$ALERT_FILE"
    echo "$ALERT_MSG" >> "$LOG_FILE"

    # Optionally: send to SIEM or webhook
    # SIEM_ENDPOINT="${CLAUDE_CODE_SIEM_ENDPOINT:-}"
    # if [[ -n "$SIEM_ENDPOINT" ]]; then
    #   curl -sf -X POST "$SIEM_ENDPOINT" \
    #     -H "Content-Type: application/json" \
    #     -d "{\"alert\":\"secret_detected\",\"type\":\"$SECRET_TYPE\",\"tool\":\"$TOOL_NAME\",\"timestamp\":\"$TIMESTAMP\"}" &>/dev/null || true
    # fi

    # Output warning to Claude (informational -- it has already run)
    echo "WARNING: Possible $SECRET_TYPE detected in tool output. Review output for accidental credential exposure before proceeding."
  fi
fi

# =============================================================================
# Track write operations for audit trail
# =============================================================================
if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
  WRITE_PATH=""
  if command -v jq &>/dev/null; then
    WRITE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null || echo "")
  fi
  echo "$TIMESTAMP | FILE_MODIFIED | path=$WRITE_PATH" >> "$LOG_FILE"
fi

# =============================================================================
# Track subprocess spawns
# =============================================================================
if [[ "$TOOL_NAME" == "Task" ]]; then
  TASK_DESC=""
  if command -v jq &>/dev/null; then
    TASK_DESC=$(echo "$INPUT" | jq -r '.tool_input.description // ""' 2>/dev/null || echo "")
  fi
  echo "$TIMESTAMP | SUBAGENT_SPAWNED | description=${TASK_DESC:0:200}" >> "$LOG_FILE"
fi

exit 0
