#!/usr/bin/env bash
# =============================================================================
# AI SAFE2 -- Devcontainer Claude Code Hardening Setup
# Runs automatically on container creation via postCreateCommand
# =============================================================================
set -euo pipefail

echo "AI SAFE2: Setting up hardened Claude Code environment..."

# Install Claude Code (native, not npm)
if ! command -v claude &>/dev/null; then
  npm install -g @anthropic-ai/claude-code@latest
fi

CLAUDE_VER=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "unknown")
echo "Claude Code version: $CLAUDE_VER"

# Create Claude directories
mkdir -p ~/.claude/hooks ~/.claude/logs

# Install hooks from repo
if [ -d ".claude-safe/hooks" ]; then
  cp .claude-safe/hooks/pre-tool-use.sh ~/.claude/hooks/
  cp .claude-safe/hooks/post-tool-use.sh ~/.claude/hooks/
  cp .claude-safe/hooks/stop.sh ~/.claude/hooks/
  chmod +x ~/.claude/hooks/*.sh
  echo "Hooks installed."
else
  echo "WARNING: .claude-safe/hooks not found. Add this repo's hooks to your project."
fi

# Install hardened settings
if [ -f ".claude-safe/settings.json" ]; then
  cp .claude-safe/settings.json ~/.claude/settings.json
  echo "Hardened settings installed."
fi

# Add env scrubbing to shell profile
PROFILE="$HOME/.bashrc"
if ! grep -q "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB" "$PROFILE" 2>/dev/null; then
  echo 'export CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1' >> "$PROFILE"
  echo "Added CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 to $PROFILE"
fi

echo ""
echo "AI SAFE2 setup complete."
echo "Run 'bash scripts/audit-installs.sh' to verify your configuration."
