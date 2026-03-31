#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Pre-Tool-Use Hook
# Sovereign Runtime Governor: Input Sanitization & Injection Detection
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# This hook runs BEFORE every Claude Code tool execution.
# Exit 0  = allow the tool use
# Exit 2  = block the tool use (stdout becomes the reason shown to Claude)
# Exit 1  = hook error (tool use proceeds -- fail open for availability)
#
# Claude Code passes tool input as JSON via stdin:
# {"tool_name": "Bash", "tool_input": {"command": "..."}, ...}
# =============================================================================

set -euo pipefail

LOG_DIR="${CLAUDE_CODE_LOG_DIR:-$HOME/.claude/logs}"
LOG_FILE="$LOG_DIR/pre-tool-use.log"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Read stdin (tool use JSON)
INPUT=$(cat)

# Extract fields -- works with or without jq
if command -v jq &>/dev/null; then
  TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // .tool_use.name // "unknown"' 2>/dev/null || echo "unknown")
  TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // .tool_use.input // {}' 2>/dev/null || echo "{}")
  BASH_CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
  FETCH_URL=$(echo "$INPUT" | jq -r '.tool_input.url // ""' 2>/dev/null || echo "")
  WRITE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null || echo "")
else
  # Fallback: grep-based extraction (less precise but functional without jq)
  TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "unknown")
  BASH_CMD=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
  FETCH_URL=$(echo "$INPUT" | grep -o '"url"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
  WRITE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
  # TOOL_INPUT available via $INPUT for pattern matching below
fi

# Log all tool use attempts
echo "$TIMESTAMP | ATTEMPT | tool=$TOOL_NAME | cmd=${BASH_CMD:0:200} | url=${FETCH_URL:0:200} | path=${WRITE_PATH:0:200}" >> "$LOG_FILE"

# =============================================================================
# BLOCK RULE: Dangerous bypass activation
# =============================================================================
block_with_reason() {
  local reason="$1"
  echo "$TIMESTAMP | BLOCKED | tool=$TOOL_NAME | reason=$reason | input=${INPUT:0:500}" >> "$LOG_FILE"
  echo "BLOCKED by AI SAFE2 Sovereign Runtime Governor: $reason"
  echo "If this is a legitimate operation, discuss it with your security team."
  exit 2
}

# =============================================================================
# Bash command checks
# =============================================================================
if [[ "$TOOL_NAME" == "Bash" ]] && [[ -n "$BASH_CMD" ]]; then

  # --- Bypass mode activation attempts ---
  if echo "$BASH_CMD" | grep -qiE 'dangerously.skip.permissions|bypass.permissions|yolo.mode'; then
    block_with_reason "Attempt to activate permission bypass mode detected"
  fi

  # --- Curl/wget pipe to shell (classic supply chain attack) ---
  if echo "$BASH_CMD" | grep -qE '(curl|wget)[^|]*\|[[:space:]]*(ba)?sh'; then
    block_with_reason "Pipe-to-shell pattern detected: curl/wget output piped directly to shell execution"
  fi

  # --- Base64 decode pipe to shell (obfuscated injection) ---
  if echo "$BASH_CMD" | grep -qE 'base64[[:space:]]+-d[^|]*\|' || \
     echo "$BASH_CMD" | grep -qE 'base64[[:space:]]+--decode[^|]*\|'; then
    block_with_reason "Base64-decode pipe pattern detected: possible obfuscated command injection"
  fi

  # --- Python/perl/ruby -c one-liner executing downloaded content ---
  if echo "$BASH_CMD" | grep -qE '(python|python3|perl|ruby)[[:space:]]+-[ce][[:space:]]+.*(\bcurl\b|\bwget\b)'; then
    block_with_reason "Script interpreter executing downloaded content detected"
  fi

  # --- Credential exfiltration via curl with env vars ---
  if echo "$BASH_CMD" | grep -qE '(env|printenv|echo[[:space:]]+\$)[^;]*\|[^;]*(curl|wget|nc|ncat)'; then
    block_with_reason "Environment variable exfiltration pattern detected (env | curl / printenv | curl)"
  fi

  # --- Direct API key exfiltration patterns ---
  if echo "$BASH_CMD" | grep -qiE '(ANTHROPIC_API_KEY|AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY|GOOGLE_APPLICATION_CREDENTIALS|AZURE_CLIENT_SECRET|GITHUB_TOKEN)[^;]*\|?[[:space:]]*(curl|wget|nc)'; then
    block_with_reason "Credential exfiltration attempt: API key or secret variable referenced in network command"
  fi

  # --- Recursive deletion of root or home ---
  if echo "$BASH_CMD" | grep -qE 'rm[[:space:]]+-[rRf]{1,3}[[:space:]]*(--[[:space:]]+)?[/~]($|[[:space:]])'; then
    block_with_reason "Recursive deletion of root or home directory detected"
  fi

  # --- Writing to system directories ---
  if echo "$BASH_CMD" | grep -qE '>[[:space:]]*/etc/|>>[[:space:]]*/etc/|>[[:space:]]*/bin/|>[[:space:]]*/usr/'; then
    block_with_reason "Attempt to write to system directory (/etc, /bin, /usr)"
  fi

  # --- Reading sensitive system files ---
  if echo "$BASH_CMD" | grep -qE 'cat[[:space:]]+/etc/shadow|cat[[:space:]]+/etc/passwd[[:space:]]*$|cat[[:space:]]+~/.ssh/id_'; then
    block_with_reason "Attempt to read sensitive system credential file"
  fi

  # --- Chmod 777 (world-writable) on executables ---
  if echo "$BASH_CMD" | grep -qE 'chmod[[:space:]]+[0-9]*7[[:space:]]|chmod[[:space:]]+-R[[:space:]]+[0-9]*7'; then
    block_with_reason "chmod world-writable permissions detected"
  fi

  # --- Netcat / socat reverse shell patterns ---
  if echo "$BASH_CMD" | grep -qE '(nc|ncat|netcat|socat)[[:space:]].*(-e[[:space:]]+|exec=)(ba)?sh'; then
    block_with_reason "Reverse shell pattern detected (nc/socat with shell execution)"
  fi

  # --- Unicode zero-width character obfuscation in commands ---
  if echo "$BASH_CMD" | grep -qP '[\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2060}-\x{2064}\x{FEFF}]' 2>/dev/null; then
    block_with_reason "Zero-width Unicode characters detected in command (obfuscation attempt)"
  fi

  # --- eval with variable expansion (common injection vector) ---
  if echo "$BASH_CMD" | grep -qE '\beval[[:space:]]+\$\(|\beval[[:space:]]+`'; then
    block_with_reason "eval with command substitution detected (potential injection vector)"
  fi

  # --- Git credential exposure ---
  if echo "$BASH_CMD" | grep -qE 'git[[:space:]]+config.*credential|git[[:space:]]+credential[[:space:]]+get'; then
    block_with_reason "Git credential extraction command detected"
  fi

  # --- SSH key exfiltration ---
  if echo "$BASH_CMD" | grep -qE 'cat[[:space:]]+~?/.ssh/.*[[:space:]]*(&&|\||;)[[:space:]]*(curl|wget|nc)'; then
    block_with_reason "SSH key exfiltration pattern detected"
  fi

  # --- Package manager executing remote scripts ---
  if echo "$BASH_CMD" | grep -qE 'npx[[:space:]]+-y|npm[[:space:]]+exec[[:space:]].*--yes' && \
     echo "$BASH_CMD" | grep -qE 'http'; then
    block_with_reason "Package manager executing unreviewed remote script with auto-yes flag"
  fi

fi

# =============================================================================
# WebFetch / WebSearch checks
# =============================================================================
if [[ "$TOOL_NAME" == "WebFetch" ]] && [[ -n "$FETCH_URL" ]]; then

  # Block data: URIs (can contain executable content)
  if echo "$FETCH_URL" | grep -qiE '^data:'; then
    block_with_reason "data: URI fetch blocked (can contain embedded executable content)"
  fi

  # Block file:// URIs (local file system access via WebFetch)
  if echo "$FETCH_URL" | grep -qiE '^file://'; then
    block_with_reason "file:// URI blocked in WebFetch (use Read tool for local files)"
  fi

  # Log external fetches for audit (do not block -- log for review)
  if echo "$FETCH_URL" | grep -qvE '^https?://(localhost|127\.0\.0\.1|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)'; then
    echo "$TIMESTAMP | EXTERNAL_FETCH | url=$FETCH_URL" >> "$LOG_FILE"
  fi
fi

# =============================================================================
# Write / Edit path checks
# =============================================================================
if [[ "$TOOL_NAME" == "Write" ]] || [[ "$TOOL_NAME" == "Edit" ]]; then
  if [[ -n "$WRITE_PATH" ]]; then
    # Block writes to /etc, /bin, /usr, /sys, /proc
    if echo "$WRITE_PATH" | grep -qE '^/etc/|^/bin/|^/usr/|^/sys/|^/proc/|^/boot/'; then
      block_with_reason "Write to system directory blocked: $WRITE_PATH"
    fi

    # Block overwriting SSH authorized_keys
    if echo "$WRITE_PATH" | grep -qE '\.ssh/(authorized_keys|known_hosts|config)$'; then
      block_with_reason "Write to SSH configuration file blocked: $WRITE_PATH"
    fi

    # Log writes to CI/CD config files for review
    if echo "$WRITE_PATH" | grep -qE '\.(github|gitlab-ci|jenkins|circleci)'; then
      echo "$TIMESTAMP | CICD_WRITE | path=$WRITE_PATH" >> "$LOG_FILE"
    fi
  fi
fi

# =============================================================================
# All checks passed -- allow the tool use
# =============================================================================
echo "$TIMESTAMP | ALLOWED | tool=$TOOL_NAME" >> "$LOG_FILE"
exit 0
