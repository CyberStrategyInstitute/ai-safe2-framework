#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Enterprise Deployment Script
# Deploys managed settings and hooks across multiple machines
# Framework: AI SAFE2 / AISM Level 4
# =============================================================================
# Usage:
#   Local (single machine):
#     sudo bash scripts/deploy-enterprise.sh
#
#   Remote via SSH:
#     bash scripts/deploy-enterprise.sh --remote user@host1 user@host2
#
#   Via Ansible: see managed-settings/ansible-role/ (if you add one)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

REMOTE_HOSTS=()
DRY_RUN=false
PLATFORM=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      shift
      while [[ $# -gt 0 ]] && [[ "$1" != --* ]]; do
        REMOTE_HOSTS+=("$1")
        shift
      done
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Auto-detect platform
if [[ -z "$PLATFORM" ]]; then
  case "$(uname -s)" in
    Darwin) PLATFORM="macos" ;;
    Linux)  PLATFORM="linux" ;;
    CYGWIN*|MINGW*|MSYS*) PLATFORM="windows" ;;
    *) PLATFORM="linux" ;;
  esac
fi

echo "AI SAFE2 Enterprise Deployment"
echo "Platform: $PLATFORM"
echo "Dry run: $DRY_RUN"
echo ""

# ---------------------------------------------------------------------------
# Determine paths based on platform
# ---------------------------------------------------------------------------
case "$PLATFORM" in
  linux)
    MANAGED_SETTINGS_DIR="/etc/claude-code"
    MANAGED_HOOKS_DIR="/etc/claude-code/hooks"
    MANAGED_SETTINGS_FILE="managed-settings/linux-policy.json"
    ;;
  macos)
    MANAGED_SETTINGS_DIR="/Library/Application Support/ClaudeCode"
    MANAGED_HOOKS_DIR="/Library/Application Support/ClaudeCode/hooks"
    MANAGED_SETTINGS_FILE="managed-settings/macos-policy.json"
    ;;
  windows)
    MANAGED_SETTINGS_DIR="C:/ProgramData/Anthropic/ClaudeCode"
    MANAGED_HOOKS_DIR="C:/ProgramData/Anthropic/ClaudeCode/hooks"
    MANAGED_SETTINGS_FILE="managed-settings/windows-policy.json"
    ;;
esac

# ---------------------------------------------------------------------------
# Deploy function
# ---------------------------------------------------------------------------
deploy_local() {
  local target_dir="$MANAGED_SETTINGS_DIR"
  local hooks_dir="$MANAGED_HOOKS_DIR"

  echo "Deploying to: $target_dir"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] Would create: $target_dir"
    echo "[DRY RUN] Would create: $hooks_dir"
    echo "[DRY RUN] Would copy: managed settings -> $target_dir/managed-settings.json"
    echo "[DRY RUN] Would copy: hooks -> $hooks_dir/"
    return 0
  fi

  # Create directories (may require sudo)
  mkdir -p "$target_dir" "$hooks_dir"

  # Deploy managed settings
  if [[ -f "$REPO_ROOT/$MANAGED_SETTINGS_FILE" ]]; then
    cp "$REPO_ROOT/$MANAGED_SETTINGS_FILE" "$target_dir/managed-settings.json"
    echo "Deployed: managed-settings.json"
  else
    echo "WARNING: $MANAGED_SETTINGS_FILE not found -- skipping managed settings"
  fi

  # Deploy hooks
  for hook in pre-tool-use.sh post-tool-use.sh stop.sh; do
    if [[ -f "$REPO_ROOT/hooks/$hook" ]]; then
      cp "$REPO_ROOT/hooks/$hook" "$hooks_dir/$hook"
      chmod +x "$hooks_dir/$hook"
      echo "Deployed hook: $hook"
    fi
  done

  # Update managed settings to use system hooks path
  if [[ -f "$target_dir/managed-settings.json" ]]; then
    if command -v python3 &>/dev/null; then
      python3 - << PYEOF
import json, re

with open("$target_dir/managed-settings.json", "r") as f:
    content = f.read()

# Replace hook paths with absolute system paths
content = content.replace("~/.claude/hooks/", "$hooks_dir/")
content = content.replace("/etc/claude-code/hooks/", "$hooks_dir/")
content = content.replace("/Library/Application Support/ClaudeCode/hooks/", "$hooks_dir/")

with open("$target_dir/managed-settings.json", "w") as f:
    f.write(content)
print("Updated hook paths in managed-settings.json")
PYEOF
    fi
  fi

  echo ""
  echo "Deployment complete."
  echo "Managed settings: $target_dir/managed-settings.json"
  echo "Hooks: $hooks_dir/"
  echo ""
  echo "Verify: bash $REPO_ROOT/scripts/audit-installs.sh"
}

# ---------------------------------------------------------------------------
# Remote deployment
# ---------------------------------------------------------------------------
deploy_remote() {
  local host="$1"
  echo "Deploying to remote host: $host"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] Would SSH to $host and deploy"
    return 0
  fi

  # Copy the repo to the remote host
  ssh "$host" "mkdir -p /tmp/ai-safe2-deploy"
  scp -r "$REPO_ROOT/hooks" "$REPO_ROOT/managed-settings" "$REPO_ROOT/scripts" \
    "$host:/tmp/ai-safe2-deploy/"

  # Run deployment on remote
  ssh "$host" "cd /tmp/ai-safe2-deploy && sudo bash scripts/deploy-enterprise.sh --platform $PLATFORM"

  echo "Remote deployment complete: $host"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if [[ ${#REMOTE_HOSTS[@]} -gt 0 ]]; then
  for host in "${REMOTE_HOSTS[@]}"; do
    deploy_remote "$host"
  done
else
  # Check if we need sudo for system paths
  if [[ "$PLATFORM" != "windows" ]] && [[ ! -w "$(dirname "$MANAGED_SETTINGS_DIR")" ]]; then
    if [[ "$DRY_RUN" == "false" ]]; then
      echo "Note: Deployment to $MANAGED_SETTINGS_DIR requires write access."
      echo "If this fails, re-run with sudo."
    fi
  fi
  deploy_local
fi
