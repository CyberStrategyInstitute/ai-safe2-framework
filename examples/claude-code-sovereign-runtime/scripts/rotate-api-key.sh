#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Emergency Credential Rotation
# Pillar 3: Fail-Safe & Recovery
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# Run this if you suspect your Anthropic API key was exposed.
# CVE-2026-21852 (pre-trust requests) and the source map leak
# make this a realistic scenario.
#
# This script:
#   1. Kills any running Claude Code processes
#   2. Helps you identify where your key is stored
#   3. Guides you through rotation
#   4. Scans for the old key in git history
# =============================================================================

set -uo pipefail

echo "================================================================"
echo "AI SAFE2 -- Emergency Credential Rotation"
echo "================================================================"
echo ""
echo "This script helps rotate your Anthropic API key after a"
echo "suspected exposure. Run through all steps."
echo ""

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# =============================================================================
# Step 1: Kill Claude Code
# =============================================================================
echo "Step 1: Stopping all Claude Code processes..."
KILLED=0

# Kill by process name
pkill -f "claude-code" 2>/dev/null && KILLED=1 || true
pkill -f "@anthropic-ai/claude-code" 2>/dev/null && KILLED=1 || true
pkill -f "claude --" 2>/dev/null && KILLED=1 || true

# Kill Node processes running Claude
pgrep -f "node.*claude" 2>/dev/null | while read -r pid; do
  kill "$pid" 2>/dev/null && echo "  Killed PID $pid" && KILLED=1 || true
done

if [[ "$KILLED" -eq 1 ]]; then
  echo "  Stopped Claude Code processes"
else
  echo "  No running Claude Code processes found"
fi

sleep 1
echo ""

# =============================================================================
# Step 2: Identify where the key is stored
# =============================================================================
echo "Step 2: Locating stored API key..."

KEY_LOCATIONS=()

# Shell profiles
for profile in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.zprofile"; do
  if [[ -f "$profile" ]] && grep -q "ANTHROPIC_API_KEY" "$profile" 2>/dev/null; then
    KEY_LOCATIONS+=("$profile")
    echo "  Found in: $profile"
  fi
done

# .env files in current and parent directories
for envfile in ".env" ".env.local" ".env.development" "$HOME/.env"; do
  if [[ -f "$envfile" ]] && grep -q "ANTHROPIC_API_KEY" "$envfile" 2>/dev/null; then
    KEY_LOCATIONS+=("$envfile")
    echo "  Found in: $envfile"
  fi
done

# Claude config
CLAUDE_CONFIG="$HOME/.config/anthropic/config.json"
if [[ -f "$CLAUDE_CONFIG" ]]; then
  echo "  Claude config exists: $CLAUDE_CONFIG (key may be stored here)"
  KEY_LOCATIONS+=("$CLAUDE_CONFIG")
fi

if [[ ${#KEY_LOCATIONS[@]} -eq 0 ]]; then
  echo "  Key not found in common locations (may be in system keychain)"
fi
echo ""

# =============================================================================
# Step 3: Rotate the key
# =============================================================================
echo "Step 3: Rotate your API key"
echo ""
echo "  MANUAL ACTION REQUIRED:"
echo "  1. Go to: https://console.anthropic.com/settings/keys"
echo "  2. Find your current API key"
echo "  3. Click 'Revoke' or 'Delete'"
echo "  4. Click 'Create Key' to generate a new one"
echo "  5. Copy the new key (you will only see it once)"
echo ""
read -r -p "Press Enter when you have revoked the old key and have the new key ready..."
echo ""

read -r -s -p "Paste your new Anthropic API key (input hidden): " NEW_KEY
echo ""

if [[ -z "$NEW_KEY" ]]; then
  echo "No key provided -- skipping update step"
else
  # Validate format
  if echo "$NEW_KEY" | grep -qE '^sk-ant-[a-zA-Z0-9\-_]{90,}$'; then
    echo "  Key format looks valid."
  else
    echo "  WARNING: Key format does not match expected pattern (sk-ant-...)."
    echo "  Verify you copied the full key."
  fi

  # Update in shell profiles
  for profile in "${KEY_LOCATIONS[@]}"; do
    if [[ -f "$profile" ]] && grep -q "ANTHROPIC_API_KEY" "$profile" 2>/dev/null; then
      if [[ "$profile" != *"config.json"* ]]; then
        # Create backup
        cp "$profile" "${profile}.bak.${TIMESTAMP//:/}"
        # Replace the key
        sed -i.tmp "s|ANTHROPIC_API_KEY=sk-ant-[^\"' ]*|ANTHROPIC_API_KEY=$NEW_KEY|g" "$profile" && \
          echo "  Updated: $profile (backup at ${profile}.bak.${TIMESTAMP//:/})" || \
          echo "  Could not auto-update $profile -- update manually"
        rm -f "${profile}.tmp"
      fi
    fi
  done

  # Export for current session
  export ANTHROPIC_API_KEY="$NEW_KEY"
  echo "  Exported new key to current session."
fi
echo ""

# =============================================================================
# Step 4: Scan git history for old key exposure
# =============================================================================
echo "Step 4: Scanning git history for credential exposure..."
echo "  (This checks recent commits where Claude Code was active)"
echo ""

if command -v git &>/dev/null && git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
  echo "  Scanning current repo..."
  LEAKS=$(git log --oneline -50 --all 2>/dev/null | while read -r hash msg; do
    HASH=$(echo "$hash $msg" | awk '{print $1}')
    git show "$HASH" 2>/dev/null | grep -E "(sk-ant-|AKIA[0-9A-Z]{16}|ghp_)" | head -3 || true
  done)

  if [[ -n "$LEAKS" ]]; then
    echo "  POTENTIAL LEAKS FOUND IN GIT HISTORY:"
    echo "$LEAKS" | head -20
    echo ""
    echo "  ACTION: Use git-filter-repo or BFG Repo Cleaner to remove secrets from history"
    echo "  Then force-push and rotate all exposed credentials"
  else
    echo "  No obvious credentials found in recent 50 commits"
  fi
else
  echo "  Not in a git repository -- skipping git scan"
fi

echo ""
echo "================================================================"
echo "Rotation complete. Summary:"
echo "  Processes stopped: yes"
echo "  Key locations found: ${#KEY_LOCATIONS[@]}"
echo "  Timestamp: $TIMESTAMP"
echo ""
echo "Next steps:"
echo "  1. Start a new terminal session to pick up the new key"
echo "  2. Re-run: bash scripts/audit-installs.sh"
echo "  3. Monitor $HOME/.claude/logs/security-alerts.log"
echo "================================================================"
