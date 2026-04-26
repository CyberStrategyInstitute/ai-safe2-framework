#!/usr/bin/env bash
set -euo pipefail

PROFILE="${PROFILE:-default}"
SESSION_TIMEOUT="${CODEX_SESSION_TIMEOUT_SECONDS:-3600}"
LOG_ROOT="${CODEX_SOVEREIGN_LOG_ROOT:-$HOME/.codex/logs}"
NOTIFY_SCRIPT="${CODEX_NOTIFY_SCRIPT:-$HOME/.codex/monitoring/codex-notify.ps1}"

mkdir -p "$LOG_ROOT"

SESSION_ID="codex-$(date +%s)-$$"
SESSION_LOG="$LOG_ROOT/wrapper-sessions.log"
SUMMARY_PATH="$LOG_ROOT/$SESSION_ID.summary.txt"

for arg in "$@"; do
  if [[ "$arg" == "--dangerously-bypass-approvals-and-sandbox" ]]; then
    echo "Blocked by AI SAFE2: dangerous bypass mode is not allowed."
    exit 2
  fi
  if [[ "$arg" == "danger-full-access" ]]; then
    echo "Blocked by AI SAFE2: danger-full-access is not allowed in the managed wrapper."
    exit 2
  fi
done

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

echo "$(timestamp) | SESSION_START | id=$SESSION_ID | profile=$PROFILE | timeout=$SESSION_TIMEOUT | args=$*" >> "$SESSION_LOG"

cleanup() {
  local exit_code=$?
  echo "$(timestamp) | SESSION_END | id=$SESSION_ID | exit_code=$exit_code" >> "$SESSION_LOG"
  printf 'SessionId=%s\nExitCode=%s\nProfile=%s\n' "$SESSION_ID" "$exit_code" "$PROFILE" > "$SUMMARY_PATH"
}

trap cleanup EXIT

(
  sleep "$SESSION_TIMEOUT"
  pkill -P $$ codex 2>/dev/null || true
) &
WATCHDOG_PID=$!

export CODEX_SOVEREIGN_SESSION_ID="$SESSION_ID"
export CODEX_SOVEREIGN_SUMMARY_PATH="$SUMMARY_PATH"
export CODEX_SOVEREIGN_LOG_ROOT="$LOG_ROOT"

codex -p "$PROFILE" \
  -c "notify=['powershell','-ExecutionPolicy','Bypass','-File','$NOTIFY_SCRIPT']" \
  "$@"

EXIT_CODE=$?
kill "$WATCHDOG_PID" 2>/dev/null || true
wait "$WATCHDOG_PID" 2>/dev/null || true
exit "$EXIT_CODE"
