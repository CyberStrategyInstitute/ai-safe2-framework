#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${HOME}/.codex"
MONITORING_ROOT="${TARGET_ROOT}/monitoring"

mkdir -p "$TARGET_ROOT" "$MONITORING_ROOT"
cp "./managed-settings/config.strict.toml" "${TARGET_ROOT}/config.toml"
cp "./monitoring/codex-notify.ps1" "${MONITORING_ROOT}/codex-notify.ps1"

echo "AI SAFE2 Codex setup complete."
echo "Next step: run ./scripts/codex-jit-wrapper.sh"
