#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${HOME}/.codex"
MONITORING_ROOT="${TARGET_ROOT}/monitoring"

mkdir -p "$TARGET_ROOT" "$MONITORING_ROOT"
cp "./monitoring/codex-notify.ps1" "${MONITORING_ROOT}/codex-notify.ps1"

echo "AI SAFE2 Codex Sovereign Runtime v2 setup complete."
echo "Installed: ${HOME}/.codex/monitoring/codex-notify.ps1"
echo "Default deployment mode: wrapper-first."
echo "Optional governance files should be copied into the target project root."
echo "Next step: run ./scripts/codex-jit-wrapper.sh"
