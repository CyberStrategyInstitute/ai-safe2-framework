#!/usr/bin/env bash
# =============================================================================
# rotate-credentials.sh — Emergency Credential Rotation
# Hermes Sovereign Runtime (HSR) | AI SAFE² v3.0
# Cyber Strategy Institute
#
# PURPOSE: Immediately rotate all credentials accessible to Hermes Agent.
# Run this immediately on any suspicion of credential exposure.
# DOES NOT require Hermes to be running.
#
# Usage:
#   ./scripts/rotate-credentials.sh                  # Interactive rotation
#   ./scripts/rotate-credentials.sh --emergency       # No-prompt emergency mode
#   ./scripts/rotate-credentials.sh --vault-only      # Rotate only Vault tokens
#   ./scripts/rotate-credentials.sh --env-only        # Rotate only .env credentials
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HSR_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${HSR_ROOT}/.env"
ROTATION_LOG="${HSR_ROOT}/logs/credential_rotation.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Flags
EMERGENCY_MODE=false
VAULT_ONLY=false
ENV_ONLY=false

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
for arg in "$@"; do
    case $arg in
        --emergency) EMERGENCY_MODE=true ;;
        --vault-only) VAULT_ONLY=true ;;
        --env-only) ENV_ONLY=true ;;
        --help)
            echo "Usage: $0 [--emergency] [--vault-only] [--env-only]"
            exit 0
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "$ROTATION_LOG")"
log() {
    local level="$1"
    local message="$2"
    echo "[${TIMESTAMP}] [${level}] ${message}" >> "$ROTATION_LOG"
    case $level in
        CRITICAL) echo -e "${RED}[CRITICAL]${NC} ${message}" ;;
        WARN)     echo -e "${YELLOW}[WARN]${NC} ${message}" ;;
        OK)       echo -e "${GREEN}[OK]${NC} ${message}" ;;
        INFO)     echo -e "${CYAN}[INFO]${NC} ${message}" ;;
    esac
}

header() {
    echo -e "\n${BOLD}${CYAN}$1${NC}"
    echo "$(echo "$1" | sed 's/./─/g')"
}

# ---------------------------------------------------------------------------
# Pre-rotation: Activate kill switch
# ---------------------------------------------------------------------------
activate_kill_switch() {
    header "Activating Kill Switch"
    local kill_signal="/var/run/hsr/kill.signal"
    mkdir -p "$(dirname "$kill_signal")"
    echo "ROTATION_IN_PROGRESS:${TIMESTAMP}" > "$kill_signal"
    log "INFO" "Kill switch activated — all Hermes tool execution suspended during rotation"
    echo -e "${GREEN}Kill switch active. Hermes tool execution suspended.${NC}"
}

# ---------------------------------------------------------------------------
# Rotate Vault tokens
# ---------------------------------------------------------------------------
rotate_vault_tokens() {
    header "Rotating HashiCorp Vault Tokens"

    if ! command -v vault &>/dev/null; then
        log "WARN" "Vault CLI not found — skipping Vault token rotation"
        echo -e "${YELLOW}Vault CLI not installed. Rotate tokens manually via Vault UI.${NC}"
        return 1
    fi

    if [[ -z "${VAULT_ADDR:-}" ]]; then
        source "${ENV_FILE}" 2>/dev/null || true
    fi

    if [[ -z "${VAULT_ADDR:-}" ]]; then
        log "WARN" "VAULT_ADDR not set — skipping Vault rotation"
        return 1
    fi

    log "INFO" "Rotating Vault token for Hermes agent"
    if vault token renew &>/dev/null; then
        log "OK" "Vault token renewed"
        echo -e "${GREEN}Vault token renewed${NC}"
    else
        log "WARN" "Could not renew Vault token — may need re-login"
        echo -e "${YELLOW}Vault token renewal failed. Login required: vault login${NC}"
    fi

    # Revoke old Hermes accessor token and issue new ephemeral token
    if [[ -n "${VAULT_HERMES_ACCESSOR:-}" ]]; then
        vault token revoke -accessor "${VAULT_HERMES_ACCESSOR}" 2>/dev/null || true
        log "INFO" "Revoked old Hermes Vault accessor: ${VAULT_HERMES_ACCESSOR}"
    fi

    # Issue new 1-hour ephemeral token for Hermes
    local new_token
    new_token=$(vault token create \
        -policy="hermes-runtime" \
        -ttl="1h" \
        -renewable=false \
        -format=json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['auth']['client_token'])" 2>/dev/null || echo "")

    if [[ -n "$new_token" ]]; then
        # Update running container if possible
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "hermes"; then
            docker exec hermes sh -c "echo 'VAULT_TOKEN=${new_token}' >> /tmp/vault_token" 2>/dev/null || true
        fi
        log "OK" "New ephemeral Vault token issued for Hermes (1-hour TTL)"
        echo -e "${GREEN}New ephemeral Vault token issued (1h TTL)${NC}"
    fi
}

# ---------------------------------------------------------------------------
# Rotate .env API credentials
# ---------------------------------------------------------------------------
rotate_env_credentials() {
    header "Rotating .env API Credentials"

    if [[ ! -f "$ENV_FILE" ]]; then
        log "WARN" ".env file not found at ${ENV_FILE}"
        return 1
    fi

    # Backup current .env
    local backup="${ENV_FILE}.backup.${TIMESTAMP//[:]/-}"
    cp "$ENV_FILE" "$backup"
    chmod 600 "$backup"
    log "INFO" ".env backed up to ${backup}"

    echo -e "${YELLOW}The following credentials need to be rotated in your provider consoles:${NC}\n"

    # Identify which credentials exist
    local creds=()
    grep -E "^(ANTHROPIC|OPENAI|OPENROUTER|GEMINI|HUGGINGFACE)_API_KEY=" "$ENV_FILE" | while IFS='=' read -r key value; do
        if [[ -n "$value" && "$value" != '""' && "$value" != "''" ]]; then
            creds+=("$key")
            echo -e "  ${BOLD}${key}${NC}"
            echo -e "    Current (masked): ${value:0:8}***${value: -4}"
            echo -e "    Rotate at:"
            case $key in
                ANTHROPIC_API_KEY) echo "    → https://console.anthropic.com/settings/keys" ;;
                OPENAI_API_KEY) echo "    → https://platform.openai.com/api-keys" ;;
                OPENROUTER_API_KEY) echo "    → https://openrouter.ai/settings/keys" ;;
                GEMINI_API_KEY) echo "    → https://aistudio.google.com/app/apikey" ;;
                HUGGINGFACE_API_KEY) echo "    → https://huggingface.co/settings/tokens" ;;
            esac
            echo ""
        fi
    done

    if [[ "$EMERGENCY_MODE" == "false" ]]; then
        echo -e "${CYAN}Rotate each key in the console above, then update .env with new values.${NC}"
        echo -e "${CYAN}Press ENTER when complete to validate new credentials...${NC}"
        read -r
    fi

    # Re-source .env with potentially updated values
    set -a
    source "$ENV_FILE" 2>/dev/null || true
    set +a

    log "OK" ".env credential rotation completed"
    echo -e "${GREEN}.env credentials updated${NC}"
}

# ---------------------------------------------------------------------------
# Clear Hermes memory of any cached credentials
# ---------------------------------------------------------------------------
clear_memory_credentials() {
    header "Scanning and Clearing Credential Artifacts from Memory"

    local memory_dir="${HOME}/.hermes/memories"
    if [[ ! -d "$memory_dir" ]]; then
        log "INFO" "No Hermes memory directory found — skipping"
        return 0
    fi

    # Find and quarantine memory files containing credential patterns
    local quarantine_dir="${HSR_ROOT}/quarantine/memory_${TIMESTAMP//[:]/-}"
    mkdir -p "$quarantine_dir"

    local count=0
    while IFS= read -r -d '' file; do
        if grep -qEi '(sk-[a-z0-9]{48}|AKIA[0-9A-Z]{16}|-----BEGIN|ghp_[a-zA-Z0-9]{36}|eyJ[a-zA-Z0-9+/]+\.[a-zA-Z0-9+/]+)' "$file" 2>/dev/null; then
            mv "$file" "$quarantine_dir/"
            log "CRITICAL" "Quarantined memory file containing credential pattern: ${file}"
            count=$((count + 1))
        fi
    done < <(find "$memory_dir" -type f -print0 2>/dev/null)

    if [[ $count -gt 0 ]]; then
        echo -e "${RED}[CRITICAL] ${count} memory file(s) containing credential patterns quarantined to:${NC}"
        echo "  ${quarantine_dir}"
        echo -e "${YELLOW}Review quarantined files and determine scope of exposure.${NC}"
    else
        log "OK" "No credential patterns found in memory store"
        echo -e "${GREEN}Memory store clean — no credential patterns found${NC}"
    fi
}

# ---------------------------------------------------------------------------
# Restart Hermes with fresh credentials
# ---------------------------------------------------------------------------
restart_hermes() {
    header "Restarting Hermes with Fresh Credentials"

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "hermes"; then
        docker restart hermes 2>/dev/null && \
            log "OK" "Hermes container restarted" && \
            echo -e "${GREEN}Hermes restarted${NC}" || \
            log "WARN" "Could not restart Hermes container automatically"
    else
        log "INFO" "Hermes container not running — manual restart required after rotation"
        echo -e "${YELLOW}Restart Hermes manually: docker-compose up -d hermes${NC}"
    fi
}

# ---------------------------------------------------------------------------
# Deactivate kill switch
# ---------------------------------------------------------------------------
deactivate_kill_switch() {
    header "Deactivating Kill Switch"
    local kill_signal="/var/run/hsr/kill.signal"
    rm -f "$kill_signal"
    log "INFO" "Kill switch deactivated — Hermes tool execution resumed"
    echo -e "${GREEN}Kill switch cleared. Hermes tool execution resumed.${NC}"
}

# ---------------------------------------------------------------------------
# Rotation summary
# ---------------------------------------------------------------------------
print_summary() {
    header "Rotation Complete"
    echo ""
    echo -e "  ${BOLD}Timestamp:${NC}    ${TIMESTAMP}"
    echo -e "  ${BOLD}Log:${NC}          ${ROTATION_LOG}"
    echo ""
    echo -e "${YELLOW}REQUIRED FOLLOW-UP ACTIONS:${NC}"
    echo "  1. Verify Hermes can authenticate to LLM provider"
    echo "  2. Run pre-flight check: ./scripts/pre-flight-check.sh"
    echo "  3. Check gateway health: curl http://localhost:8000/hsr/health"
    echo "  4. Review quarantine directory for any exposed credentials"
    echo "  5. File a security event record in your ITSM system"
    echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    echo -e "${BOLD}${RED}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║         HSR CREDENTIAL ROTATION — AI SAFE² v3.0          ║"
    echo "║              Cyber Strategy Institute                      ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    if [[ "$EMERGENCY_MODE" == "false" ]]; then
        echo -e "${YELLOW}This script will rotate all credentials accessible to Hermes Agent.${NC}"
        echo -e "${YELLOW}Hermes tool execution will be suspended during rotation.${NC}"
        echo ""
        read -p "Continue? (yes/no): " confirm
        [[ "$confirm" != "yes" ]] && { echo "Aborted."; exit 0; }
    fi

    log "INFO" "=== Credential rotation started (emergency=${EMERGENCY_MODE}) ==="

    activate_kill_switch

    if [[ "$ENV_ONLY" == "false" ]]; then
        rotate_vault_tokens || true
    fi

    if [[ "$VAULT_ONLY" == "false" ]]; then
        rotate_env_credentials || true
        clear_memory_credentials || true
    fi

    restart_hermes || true
    deactivate_kill_switch
    print_summary

    log "INFO" "=== Credential rotation completed ==="
}

main "$@"
