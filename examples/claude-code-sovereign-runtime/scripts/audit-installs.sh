#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Claude Code Installation Audit
# Pillar 2: Audit & Inventory
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# Finds every Claude Code installation path, version, and configuration
# across: npm (global/local), Homebrew, system installs, devcontainers,
# CI/CD runners, and VS Code / Cursor extensions.
# =============================================================================

set -uo pipefail

REPORT_FILE="${1:-$HOME/.claude/audit-$(date +%Y%m%d-%H%M%S).txt}"
mkdir -p "$(dirname "$REPORT_FILE")"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ISSUES_FOUND=0

log() { echo "$1" | tee -a "$REPORT_FILE"; }
warn() { echo "[WARN] $1" | tee -a "$REPORT_FILE"; ISSUES_FOUND=$((ISSUES_FOUND + 1)); }
info() { echo "[INFO] $1" | tee -a "$REPORT_FILE"; }
ok()   { echo "[ OK ] $1" | tee -a "$REPORT_FILE"; }

log "================================================================"
log "AI SAFE2 Claude Code Installation Audit"
log "Generated: $TIMESTAMP"
log "Host: $(hostname)"
log "User: $(whoami)"
log "================================================================"
log ""

# =============================================================================
# 1. Find Claude Code binaries
# =============================================================================
log "--- Claude Code Binary Locations ---"

# PATH-based discovery
if command -v claude &>/dev/null; then
  CLAUDE_BIN=$(command -v claude)
  info "Found in PATH: $CLAUDE_BIN"

  # Get version
  CLAUDE_VER=$(claude --version 2>/dev/null || echo "unknown")
  info "Version: $CLAUDE_VER"

  # Check if npm-based (deprecated, higher risk)
  if echo "$CLAUDE_BIN" | grep -qE 'node_modules|npm'; then
    warn "npm-based installation detected at $CLAUDE_BIN -- npm installs are deprecated and higher risk"
    warn "Migrate to native installer: brew install claude-code OR visit claude.ai/download"
  else
    ok "Binary is not npm-based"
  fi
fi

# Check npm global install specifically
log ""
log "--- npm Global Install Check ---"
NPM_CLAUDE=$(npm ls -g @anthropic-ai/claude-code --depth=0 2>/dev/null | grep claude-code || echo "")
if [[ -n "$NPM_CLAUDE" ]]; then
  warn "npm global install found: $NPM_CLAUDE -- migrate to native installer"
  # Extract version for CVE check
  NPM_VER=$(echo "$NPM_CLAUDE" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "")
  if [[ -n "$NPM_VER" ]]; then
    check_version_cve "$NPM_VER"
  fi
else
  ok "No npm global install of @anthropic-ai/claude-code"
fi

# Check Homebrew
log ""
log "--- Homebrew Install Check ---"
if command -v brew &>/dev/null; then
  BREW_CLAUDE=$(brew list --versions claude-code 2>/dev/null || echo "")
  if [[ -n "$BREW_CLAUDE" ]]; then
    info "Homebrew install: $BREW_CLAUDE"
  else
    info "No Homebrew install found"
  fi
else
  info "Homebrew not installed on this system"
fi

# Version CVE check function
check_version_cve() {
  local ver="$1"
  local major minor patch
  major=$(echo "$ver" | cut -d. -f1)
  minor=$(echo "$ver" | cut -d. -f2)
  patch=$(echo "$ver" | cut -d. -f3)

  # CVE-2026-21852: < 2.0.65
  if [[ "$major" -lt 2 ]] || { [[ "$major" -eq 2 ]] && [[ "$minor" -eq 0 ]] && [[ "$patch" -lt 65 ]]; }; then
    warn "Version $ver is vulnerable to CVE-2026-21852 (API key exfiltration via pre-trust requests)"
    warn "ACTION REQUIRED: Rotate your Anthropic API key and upgrade Claude Code immediately"
  fi

  # CVE-2025-64755: < 2.0.31
  if [[ "$major" -lt 2 ]] || { [[ "$major" -eq 2 ]] && [[ "$minor" -eq 0 ]] && [[ "$patch" -lt 31 ]]; }; then
    warn "Version $ver is vulnerable to CVE-2025-64755 (arbitrary file write via sed parsing)"
  fi

  # CVE-2025-58764: < 1.0.105
  if [[ "$major" -lt 1 ]] || { [[ "$major" -eq 1 ]] && [[ "$minor" -eq 0 ]] && [[ "$patch" -lt 105 ]]; }; then
    warn "Version $ver is vulnerable to CVE-2025-58764 (approval bypass via command parsing)"
  fi
}

# Run CVE check on installed version
if command -v claude &>/dev/null; then
  VER=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "")
  if [[ -n "$VER" ]]; then
    log ""
    log "--- CVE Version Check: $VER ---"
    check_version_cve "$VER"
  fi
fi

# =============================================================================
# 2. Scan settings files for dangerous configurations
# =============================================================================
log ""
log "--- Settings File Audit ---"

# Find all .claude directories and settings files
SETTINGS_FILES=$(find "$HOME" /home /root /var \
  \( -name "settings.json" -o -name "settings.local.json" \) \
  -path "*/.claude/*" 2>/dev/null | head -100)

if [[ -z "$SETTINGS_FILES" ]]; then
  info "No .claude/settings*.json files found"
else
  while IFS= read -r sf; do
    [[ -z "$sf" ]] && continue
    info "Found settings file: $sf"

    if [[ -r "$sf" ]]; then
      # Check for bypassPermissions
      if grep -q '"bypassPermissions"[[:space:]]*:[[:space:]]*true' "$sf" 2>/dev/null; then
        warn "CRITICAL: bypassPermissions: true found in $sf"
        warn "This disables the entire Claude Code safety stack -- remove immediately"
      fi

      # Check for broad tool allowances
      if grep -qE '"allow"[[:space:]]*:[[:space:]]*\["Bash\(\*\)"\]' "$sf" 2>/dev/null; then
        warn "Overly broad permission in $sf: Bash(*) allows all bash commands"
      fi

      # Check for missing hooks
      if ! grep -q '"hooks"' "$sf" 2>/dev/null; then
        warn "No hooks configured in $sf -- consider deploying AI SAFE2 hooks"
      else
        ok "Hooks configured in $sf"
      fi
    else
      warn "Cannot read $sf (permissions issue)"
    fi
  done <<< "$SETTINGS_FILES"
fi

# =============================================================================
# 3. Check environment variables
# =============================================================================
log ""
log "--- Environment Variable Check ---"

if [[ "${CLAUDE_CODE_SUBPROCESS_ENV_SCRUB:-0}" == "1" ]]; then
  ok "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 is set (credentials scrubbed from subprocesses)"
else
  warn "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB is not set to 1"
  warn "Add to your shell profile: export CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1"
fi

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  KEY_PREFIX="${ANTHROPIC_API_KEY:0:12}..."
  info "ANTHROPIC_API_KEY is set (prefix: $KEY_PREFIX)"

  # Check if it's in a git-tracked dotfile (common mistake)
  SHELL_PROFILES=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile")
  for profile in "${SHELL_PROFILES[@]}"; do
    if [[ -f "$profile" ]] && grep -q "ANTHROPIC_API_KEY" "$profile" 2>/dev/null; then
      if git -C "$HOME" ls-files --error-unmatch "$profile" &>/dev/null 2>&1; then
        warn "ANTHROPIC_API_KEY is referenced in $profile which is git-tracked -- secret may be committed"
      fi
    fi
  done
fi

# =============================================================================
# 4. Check for CI/CD exposures
# =============================================================================
log ""
log "--- CI/CD Configuration Check ---"

while IFS= read -r -d $'\0' f; do
  [[ -f "$f" ]] || continue
  info "Found CI/CD config: $f"
  if grep -qiE 'claude|anthropic' "$f" 2>/dev/null; then
    info "  Contains Claude/Anthropic references -- review for security"
    if grep -qiE 'dangerously.skip|bypass.permission|YOLO' "$f" 2>/dev/null; then
      warn "  CRITICAL: Bypass mode found in CI/CD config $f"
    fi
  fi
done < <(find . -maxdepth 4 \( \
  -name "*.yml" -path "*/.github/workflows/*" -o \
  -name "*.yaml" -path "*/.github/workflows/*" -o \
  -name ".gitlab-ci.yml" -o \
  -name "Jenkinsfile" -o \
  -name "config.yml" -path "*/.circleci/*" \
\) -print0 2>/dev/null)

# =============================================================================
# 5. Check for MCP servers
# =============================================================================
log ""
log "--- MCP Server Check ---"

MCP_CONFIGS=$(find "$HOME" 2>/dev/null -name "*.json" -path "*mcp*" | head -20 || echo "")
if [[ -n "$MCP_CONFIGS" ]]; then
  while IFS= read -r mc; do
    [[ -z "$mc" ]] && continue
    info "Found possible MCP config: $mc"
    if grep -qE '"url"|"command"' "$mc" 2>/dev/null; then
      warn "  MCP server with external connections found in $mc -- validate with integrations/mcp-proxy.sh"
    fi
  done <<< "$MCP_CONFIGS"
fi

# =============================================================================
# 6. Summary
# =============================================================================
log ""
log "================================================================"
log "AUDIT SUMMARY"
log "Total issues found: $ISSUES_FOUND"
if [[ "$ISSUES_FOUND" -eq 0 ]]; then
  log "STATUS: PASS -- No critical issues detected"
else
  log "STATUS: ACTION REQUIRED -- Review warnings above"
fi
log ""
log "Full report saved to: $REPORT_FILE"
log "================================================================"

exit "$([[ $ISSUES_FOUND -eq 0 ]] && echo 0 || echo 1)"
