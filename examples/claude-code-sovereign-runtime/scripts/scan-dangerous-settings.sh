#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Dangerous Settings Scanner
# Pillar 2: Audit & Inventory
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# Scans for overly permissive .claude/settings*.json files across the system.
# Run this as part of your regular security hygiene and after onboarding
# new developers.
# =============================================================================

set -uo pipefail

SEARCH_ROOT="${1:-$HOME}"
REPORT_FILE="${2:-$HOME/.claude/settings-scan-$(date +%Y%m%d).txt}"
mkdir -p "$(dirname "$REPORT_FILE")"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CRITICAL=0
WARNINGS=0

echo "AI SAFE2 -- Dangerous Settings File Scanner"
echo "Generated: $TIMESTAMP"
echo "Scanning: $SEARCH_ROOT"
echo "Report: $REPORT_FILE"
echo ""

{
  echo "AI SAFE2 Settings Scanner Report"
  echo "Generated: $TIMESTAMP"
  echo "Scan root: $SEARCH_ROOT"
  echo "---"
} > "$REPORT_FILE"

# Find all Claude settings files
mapfile -t SETTINGS_FILES < <(
  find "$SEARCH_ROOT" \
    \( -name "settings.json" -o -name "settings.local.json" \) \
    -path "*/.claude/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    2>/dev/null | sort
)

if [[ ${#SETTINGS_FILES[@]} -eq 0 ]]; then
  echo "No .claude/settings*.json files found under $SEARCH_ROOT"
  exit 0
fi

echo "Found ${#SETTINGS_FILES[@]} settings file(s)"
echo ""

for sf in "${SETTINGS_FILES[@]}"; do
  echo "Checking: $sf"

  if [[ ! -r "$sf" ]]; then
    echo "  [SKIP] Cannot read file"
    continue
  fi

  FILE_ISSUES=0

  # --- CRITICAL: bypassPermissions ---
  if grep -q '"bypassPermissions"[[:space:]]*:[[:space:]]*true' "$sf" 2>/dev/null; then
    MSG="  [CRITICAL] bypassPermissions: true -- entire safety stack disabled"
    echo "$MSG"
    echo "$MSG" >> "$REPORT_FILE"
    CRITICAL=$((CRITICAL + 1))
    FILE_ISSUES=$((FILE_ISSUES + 1))
  fi

  # --- CRITICAL: permissionMode with bypass ---
  if grep -q '"permissionMode"[[:space:]]*:[[:space:]]*"bypassPermissions"' "$sf" 2>/dev/null; then
    MSG="  [CRITICAL] permissionMode: bypassPermissions -- same as bypass flag"
    echo "$MSG"
    echo "$MSG" >> "$REPORT_FILE"
    CRITICAL=$((CRITICAL + 1))
    FILE_ISSUES=$((FILE_ISSUES + 1))
  fi

  # --- WARNING: Wildcard bash allow ---
  if grep -qE '"Bash\(\*\)"' "$sf" 2>/dev/null; then
    MSG="  [WARN] Bash(*) allow -- unrestricted bash execution"
    echo "$MSG"
    echo "$MSG" >> "$REPORT_FILE"
    WARNINGS=$((WARNINGS + 1))
    FILE_ISSUES=$((FILE_ISSUES + 1))
  fi

  # --- WARNING: Network + execute + git push chain ---
  FETCH_ALLOWED=$(grep -c '"WebFetch"' "$sf" 2>/dev/null || echo 0)
  BASH_ALLOWED=$(grep -c '"Bash' "$sf" 2>/dev/null || echo 0)
  if [[ "$FETCH_ALLOWED" -gt 0 ]] && [[ "$BASH_ALLOWED" -gt 0 ]]; then
    if grep -qE '".*git.*push.*"' "$sf" 2>/dev/null; then
      MSG="  [WARN] WebFetch + Bash + git push all allowed -- potential supply chain worm vector"
      echo "$MSG"
      echo "$MSG" >> "$REPORT_FILE"
      WARNINGS=$((WARNINGS + 1))
      FILE_ISSUES=$((FILE_ISSUES + 1))
    fi
  fi

  # --- INFO: No hooks ---
  if ! grep -q '"hooks"' "$sf" 2>/dev/null; then
    MSG="  [INFO] No hooks configured -- consider deploying AI SAFE2 hooks"
    echo "$MSG"
    echo "$MSG" >> "$REPORT_FILE"
    FILE_ISSUES=$((FILE_ISSUES + 1))
  fi

  # --- INFO: autoUpdater disabled ---
  if grep -q '"autoUpdaterStatus"[[:space:]]*:[[:space:]]*"disabled"' "$sf" 2>/dev/null; then
    echo "  [ OK ] autoUpdater is disabled (good for controlled deployments)"
  fi

  # Print the file path to report
  echo "File: $sf | issues: $FILE_ISSUES" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"

  if [[ "$FILE_ISSUES" -eq 0 ]]; then
    echo "  [ OK ] No issues found"
  fi
  echo ""
done

echo "============================="
echo "SCAN SUMMARY"
echo "Files scanned: ${#SETTINGS_FILES[@]}"
echo "Critical issues: $CRITICAL"
echo "Warnings: $WARNINGS"
echo ""

{
  echo "============================="
  echo "Critical issues: $CRITICAL"
  echo "Warnings: $WARNINGS"
} >> "$REPORT_FILE"

if [[ "$CRITICAL" -gt 0 ]]; then
  echo "ACTION REQUIRED: $CRITICAL critical issue(s) found."
  echo "Immediate fix for bypassPermissions: true --"
  echo "  Edit each flagged file and set: \"bypassPermissions\": false"
  echo "  Or remove the key entirely (defaults to false)"
  exit 1
elif [[ "$WARNINGS" -gt 0 ]]; then
  echo "REVIEW REQUIRED: $WARNINGS warning(s) found. See $REPORT_FILE"
  exit 0
else
  echo "All settings files look safe."
  exit 0
fi
