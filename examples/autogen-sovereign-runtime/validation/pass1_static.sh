#!/usr/bin/env bash
# AI SAFE² v3.0 — AutoGen 0.4 Sovereign Runtime — Pass 1: Static Validation
set -euo pipefail
cd "$(dirname "$0")/.."

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
PASS=0; FAIL=0
ok()   { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)) || true; }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)) || true; }

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   AI SAFE² v3.0 — AutoGen Pass 1: Static Validation         ║"
echo "╚══════════════════════════════════════════════════════════════╝"

echo ""; echo "── 1. Python Imports ──"
python3 -c "from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier, AISAFE2Violation, CircuitTripped, AISAFE2ClassHAction" \
  && ok "ai_safe2_engine.py" || fail "ai_safe2_engine.py failed"
python3 -c "from enforcement.sovereign_autogen import CodeBlockGuard, SovereignAssistantProxy, SovereignCodeExecutorProxy, SovereignRuntime" \
  && ok "sovereign_autogen.py" || fail "sovereign_autogen.py failed"
python3 -c "from enforcement import AISAFE2Engine, SovereignRuntime, CodeBlockGuard" \
  && ok "enforcement __init__.py" || fail "__init__.py failed"

echo ""; echo "── 2. Required Files ──"
for f in enforcement/ai_safe2_engine.py enforcement/sovereign_autogen.py \
          enforcement/__init__.py smoke_test.py requirements.txt .env.example \
          controls/policy.yaml core/IDENTITY.md README.md; do
  [[ -f "$f" ]] && ok "$f" || fail "$f missing"
done

echo ""; echo "── 3. Policy YAML Control IDs ──"
for ctrl in P1.T1.2 P1.T1.5 P1.T1.10 P1.T2.3 S1.3 S1.5 F3.2 F3.5 \
            A2.5 M4.5 P2.T3.6 CP.3 CP.4 CP.8 CP.10; do
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

echo ""; echo "── 6. AutoGen-Specific Checks ──"
grep -q "CodeBlockGuard" enforcement/sovereign_autogen.py \
  && ok "CodeBlockGuard class present" || fail "CodeBlockGuard missing"
grep -q "protect_code_block" enforcement/sovereign_autogen.py \
  && ok "protect_code_block method present" || fail "protect_code_block missing"
grep -q "is_catastrophic" enforcement/sovereign_autogen.py \
  && ok "is_catastrophic method present" || fail "is_catastrophic missing"
grep -q "wrap_code_executor" enforcement/sovereign_autogen.py \
  && ok "wrap_code_executor method present" || fail "wrap_code_executor missing"
grep -q "SovereignCodeExecutorProxy" enforcement/sovereign_autogen.py \
  && ok "SovereignCodeExecutorProxy class present" || fail "SovereignCodeExecutorProxy missing"
grep -q "scan_message_content_async" enforcement/sovereign_autogen.py \
  && ok "scan_message_content_async (async path) present" || fail "async scan missing"
# CP.8 mandatory check in policy.yaml
grep -q "mandatory_for" controls/policy.yaml \
  && ok "CP.8 mandatory_for annotation in policy.yaml" || fail "CP.8 mandatory_for missing"

echo ""; echo "── 7. Dangerous Pattern Coverage ──"
python3 - << 'PYEOF'
import sys
sys.path.insert(0, '.')
from enforcement.sovereign_autogen import _PYTHON_DANGEROUS, _SHELL_DANGEROUS, _CATASTROPHIC_CODE
assert len(_PYTHON_DANGEROUS) >= 8, f"Too few Python dangerous patterns: {len(_PYTHON_DANGEROUS)}"
assert len(_SHELL_DANGEROUS) >= 8, f"Too few shell dangerous patterns: {len(_SHELL_DANGEROUS)}"
assert len(_CATASTROPHIC_CODE) >= 4, f"Too few catastrophic patterns: {len(_CATASTROPHIC_CODE)}"
print(f"  Python patterns: {len(_PYTHON_DANGEROUS)}, Shell: {len(_SHELL_DANGEROUS)}, Catastrophic: {len(_CATASTROPHIC_CODE)}")
PYEOF
[[ $? -eq 0 ]] && ok "Dangerous pattern registries populated" || fail "Pattern registries insufficient"

echo ""
echo "────────────────────────────────────────────────────────────────"
TOTAL=$((PASS + FAIL))
echo "  Pass 1 Static: $PASS/$TOTAL"
[[ $FAIL -eq 0 ]] && echo -e "  ${GREEN}✅ STATIC VALIDATION PASSED${NC}" && exit 0 \
  || { echo -e "  ${RED}❌ STATIC VALIDATION FAILED — $FAIL failing${NC}"; exit 1; }
