#!/usr/bin/env bash
# AI SAFE² v3.0 — LangChain Sovereign Runtime
# Pass 1: Static Validation
# Verifies: imports, config completeness, policy.yaml control coverage
# Usage: bash validation/pass1_static.sh
# Exit 0 = pass, Exit 1 = fail

set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0

ok()   { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)) || true; }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)) || true; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   AI SAFE² v3.0 — Pass 1: Static Validation                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ── 1. Python imports ─────────────────────────────────────────────────────
echo ""
echo "── 1. Python Imports ──"

python3 -c "from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier, AISAFE2Violation, CircuitTripped, AISAFE2ClassHAction" \
  && ok "ai_safe2_engine.py imports clean" \
  || fail "ai_safe2_engine.py import failed"

python3 -c "from enforcement.sovereign_langchain import SovereignCallbackHandler, SovereignLangChain" \
  && ok "sovereign_langchain.py imports clean" \
  || fail "sovereign_langchain.py import failed"

python3 -c "from enforcement import AISAFE2Engine, SovereignCallbackHandler, ACTTier" \
  && ok "enforcement package __init__.py exports clean" \
  || fail "enforcement __init__.py export failed"

# ── 2. Required files present ─────────────────────────────────────────────
echo ""
echo "── 2. Required Files ──"

REQUIRED_FILES=(
  "enforcement/ai_safe2_engine.py"
  "enforcement/sovereign_langchain.py"
  "enforcement/__init__.py"
  "smoke_test.py"
  "requirements.txt"
  ".env.example"
  "controls/policy.yaml"
  "core/IDENTITY.md"
  "core/SOUL.md"
  "core/TOOLS.md"
  "core/MEMORY.md"
  "README.md"
  "QUICKSTART.md"
  "SECURITY.md"
)

for f in "${REQUIRED_FILES[@]}"; do
  [[ -f "$f" ]] && ok "$f" || fail "$f missing"
done

# ── 3. policy.yaml — control coverage ────────────────────────────────────
echo ""
echo "── 3. Policy YAML: Required Control IDs ──"

REQUIRED_CONTROLS=(
  "P1.T1.2" "P1.T1.5" "P1.T1.10" "P1.T2.3"
  "S1.3" "S1.5" "F3.2" "F3.5"
  "A2.5" "M4.5" "P2.T3.6"
  "CP.3" "CP.4" "CP.8" "CP.10"
)

for ctrl in "${REQUIRED_CONTROLS[@]}"; do
  grep -q "$ctrl" controls/policy.yaml \
    && ok "controls/policy.yaml contains $ctrl" \
    || fail "controls/policy.yaml MISSING $ctrl"
done

# ── 4. No fabricated control IDs ─────────────────────────────────────────
echo ""
echo "── 4. Fabricated Control ID Check ──"

FABRICATED=("P1.INJECT" "P4.EXFIL" "P5.BAND" "P1.T1.INJECT" "P2.T4.EXFIL")
ALL_CLEAN=true
for fid in "${FABRICATED[@]}"; do
  if grep -rq "$fid" enforcement/ controls/ 2>/dev/null; then
    fail "Fabricated control ID found: $fid"
    ALL_CLEAN=false
  fi
done
[[ "$ALL_CLEAN" == true ]] && ok "No fabricated control IDs detected"

# ── 5. ACT tier enum present in engine ───────────────────────────────────
echo ""
echo "── 5. ACT Tier Completeness ──"

for tier in ACT1 ACT2 ACT3 ACT4; do
  grep -q "$tier" enforcement/ai_safe2_engine.py \
    && ok "ACT tier $tier defined in engine" \
    || fail "ACT tier $tier missing from engine"
done

# ── 6. stdlib-only engine (no external imports) ───────────────────────────
echo ""
echo "── 6. Engine External Dependency Check ──"

EXTERNAL_IMPORTS=$(python3 -c "
import ast, sys
with open('enforcement/ai_safe2_engine.py') as f:
    tree = ast.parse(f.read())
stdlib = {'re','hashlib','json','os','sys','time','uuid','enum','typing',
          'collections','datetime','pathlib','urllib','functools','abc',
          '__future__','dataclasses'}
external = []
for node in ast.walk(tree):
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        mod = node.names[0].name if isinstance(node, ast.Import) else (node.module or '')
        root = mod.split('.')[0]
        if root and root not in stdlib and not root.startswith('_'):
            external.append(root)
print('\n'.join(set(external)))
" 2>/dev/null)

if [[ -z "$EXTERNAL_IMPORTS" ]]; then
  ok "ai_safe2_engine.py — stdlib only (zero external deps)"
else
  fail "ai_safe2_engine.py has external imports: $EXTERNAL_IMPORTS"
fi

# ── 7. .env.example completeness ─────────────────────────────────────────
echo ""
echo "── 7. .env.example Keys ──"

ENV_KEYS=("AISAFE2_ACT_TIER" "AISAFE2_ALLOWED_DOMAINS" "AISAFE2_AUDIT_LOG_DIR"
          "AISAFE2_MAX_TOOL_CALLS" "AISAFE2_MAX_IDENTICAL_CALLS")
for key in "${ENV_KEYS[@]}"; do
  grep -q "$key" .env.example \
    && ok ".env.example has $key" \
    || fail ".env.example missing $key"
done

# ── Summary ───────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────────"
TOTAL=$((PASS + FAIL))
echo "  Pass 1 Static: $PASS/$TOTAL"
if [[ $FAIL -eq 0 ]]; then
  echo -e "  ${GREEN}✅ STATIC VALIDATION PASSED${NC}"
  exit 0
else
  echo -e "  ${RED}❌ STATIC VALIDATION FAILED — $FAIL check(s) failing${NC}"
  exit 1
fi
