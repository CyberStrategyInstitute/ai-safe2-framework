#!/usr/bin/env bash
# AI SAFE² v3.0 — LangGraph Sovereign Runtime
# Pass 1: Static Validation
set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
PASS=0; FAIL=0
ok()   { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)) || true; }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)) || true; }

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   AI SAFE² v3.0 — LangGraph Pass 1: Static Validation       ║"
echo "╚══════════════════════════════════════════════════════════════╝"

echo ""; echo "── 1. Python Imports ──"
python3 -c "from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier, AISAFE2Violation, CircuitTripped, AISAFE2ClassHAction" \
  && ok "ai_safe2_engine.py imports clean" || fail "ai_safe2_engine.py failed"
python3 -c "from enforcement.sovereign_langgraph import StateGuard, RoutingGuard, SovereignStateGraph" \
  && ok "sovereign_langgraph.py imports clean" || fail "sovereign_langgraph.py failed"
python3 -c "from enforcement import AISAFE2Engine, SovereignStateGraph, ACTTier" \
  && ok "enforcement __init__.py exports clean" || fail "__init__.py failed"

echo ""; echo "── 2. Required Files ──"
for f in enforcement/ai_safe2_engine.py enforcement/sovereign_langgraph.py \
          enforcement/__init__.py smoke_test.py requirements.txt .env.example \
          controls/policy.yaml core/IDENTITY.md core/SOUL.md core/TOOLS.md \
          core/MEMORY.md README.md; do
  [[ -f "$f" ]] && ok "$f" || fail "$f missing"
done

echo ""; echo "── 3. Policy YAML Control IDs ──"
for ctrl in P1.T1.2 P1.T1.5 P1.T1.10 P1.T2.3 S1.3 S1.5 F3.2 F3.5 \
            A2.5 M4.5 P2.T3.6 CP.3 CP.4 CP.9 CP.10; do
  grep -q "$ctrl" controls/policy.yaml \
    && ok "policy.yaml: $ctrl" || fail "policy.yaml MISSING $ctrl"
done

echo ""; echo "── 4. Fabricated Control ID Check ──"
CLEAN=true
for fid in P1.INJECT P4.EXFIL P5.BAND; do
  grep -rq "$fid" enforcement/ 2>/dev/null && { fail "Fabricated ID: $fid"; CLEAN=false; } || true
done
[[ "$CLEAN" == true ]] && ok "No fabricated control IDs"

echo ""; echo "── 5. Engine: Zero External Deps ──"
EXTERNAL=$(python3 - << 'PYEOF'
import ast
with open('enforcement/ai_safe2_engine.py') as f:
    tree = ast.parse(f.read())
stdlib = {'re','hashlib','json','os','sys','time','uuid','enum','typing',
          'collections','datetime','pathlib','urllib','functools','abc',
          '__future__','dataclasses'}
ext = []
for node in ast.walk(tree):
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        mod = node.names[0].name if isinstance(node, ast.Import) else (node.module or '')
        root = mod.split('.')[0]
        if root and root not in stdlib and not root.startswith('_'):
            ext.append(root)
print(','.join(set(ext)))
PYEOF
)
[[ -z "$EXTERNAL" ]] && ok "ai_safe2_engine.py stdlib only" || fail "External imports: $EXTERNAL"

echo ""; echo "── 6. CP.9 Max Depths ──"
for tier_depth in "ACT2: 5" "ACT3: 2" "ACT4: 3"; do
  grep -q "$tier_depth" controls/policy.yaml \
    && ok "CP.9 depth: $tier_depth" || fail "CP.9 missing depth: $tier_depth"
done

echo ""
echo "────────────────────────────────────────────────────────────────"
TOTAL=$((PASS + FAIL))
echo "  Pass 1 Static: $PASS/$TOTAL"
[[ $FAIL -eq 0 ]] && echo -e "  ${GREEN}✅ STATIC VALIDATION PASSED${NC}" && exit 0 \
  || { echo -e "  ${RED}❌ STATIC VALIDATION FAILED — $FAIL failing${NC}"; exit 1; }
