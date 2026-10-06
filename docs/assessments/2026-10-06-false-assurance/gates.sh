#!/usr/bin/env bash
# Local mirror of the repository's CI gates for this branch. Usage:
#   VENV=/path/to/venv OPA_BIN=... OPA_LEGACY_BIN=... GITLEAKS=... SEMGREP=... bash gates.sh [OUT_DIR]
# VENV must have: pip install -e ".[all,dev]" -e ./NEXUS -e "./skills/mcp[dev]" build pytest ruff
# Prints one line per gate: PASS / FAIL / NOT_RUN (tool absent). Exit 1 if any FAIL.
set -u
ROOT=$(git rev-parse --show-toplevel); cd "$ROOT"
OUT=${1:-$(mktemp -d)}; mkdir -p "$OUT"
PY="$VENV/bin/python"; export PATH="$VENV/bin:$PATH"
fails=0
gate() { # name, command...
  local name=$1; shift
  if "$@" >"$OUT/${name//[^A-Za-z0-9]/_}.log" 2>&1; then echo "PASS     $name"
  else echo "FAIL     $name  (log: $OUT/${name//[^A-Za-z0-9]/_}.log)"; fails=$((fails+1)); fi
}
skip() { echo "NOT_RUN  $1  ($2)"; }

# ci.yml: test
gate "pytest tests/ scanner/tests/"            "$PY" -m pytest tests/ scanner/tests/ -q -p no:cacheprovider
gate "check_agent_manifest"                    "$PY" scripts/check_agent_manifest.py
for ex in aism-decision-card aism-remediation environment-decision-card; do
  gate "example verify $ex"                    safe2 example verify "$ex"
  gate "example smoke $ex"                     "$PY" "examples/$ex/smoke_test.py"
done
gate "build sdist+wheel"                       "$PY" -m build --outdir "$OUT/dist"
# ci.yml: nexus + compliance + examples + mcp-server + lint
gate "NEXUS SDK tests"                         "$PY" -m pytest NEXUS/sdk/python/tests -q -p no:cacheprovider
if [ -n "${OPA_BIN:-}" ]; then
  gate "nexus-score --v03-checks (OPA)"        env OPA_BIN="$OPA_BIN" PYTHONPATH=NEXUS/sdk/python "$PY" NEXUS/compliance/scoring/nexus-score.py --v03-checks
  gate "opa check --strict (1.x)"              "$OPA_BIN" check --strict NEXUS/opa
  gate "opa test (1.x)"                        "$OPA_BIN" test NEXUS/opa
  gate "opa fmt (1.x)"                         "$OPA_BIN" fmt --list --fail NEXUS/opa
else skip "OPA gates" "set OPA_BIN"; fi
if [ -n "${OPA_LEGACY_BIN:-}" ]; then
  gate "opa check --strict (0.65)"             "$OPA_LEGACY_BIN" check --strict NEXUS/opa
  gate "opa test (0.65)"                       "$OPA_LEGACY_BIN" test NEXUS/opa
else skip "OPA 0.65 gates" "set OPA_LEGACY_BIN"; fi
gate "NEXUS example sovereign_gateway"         env PYTHONPATH=NEXUS/sdk/python "$PY" NEXUS/examples/sovereign_gateway.py
gate "NEXUS example acs_bridge"                env PYTHONPATH=NEXUS/sdk/python "$PY" NEXUS/examples/acs_bridge.py
gate "skills/mcp tests"                        bash -c "cd skills/mcp && '$PY' -m pytest tests -q -rs -p no:cacheprovider"
gate "ruff E9,F63,F7,F82"                      ruff check --select E9,F63,F7,F82 NEXUS/sdk/python/nexus_sdk/ NEXUS/sdk/python/tests/ NEXUS/examples/ scanner/ safe2/ aisafe2_mcp_tools/ tests/ skills/mcp/src/ scripts/
# v31-consistency.yml
gate "check_repo_ux"                           "$PY" scripts/check_repo_ux.py
gate "examples table --check"                  "$PY" scripts/generate_examples_table.py --check
gate "v31 MCP profile tests"                   "$PY" -m pytest scanner/tests/test_v31_mcp_profile.py -q -p no:cacheprovider
gate "v31 persistence compat"                  "$PY" -m pytest NEXUS/sdk/python/tests/test_v31_persistence_compat.py -q -p no:cacheprovider
gate "MCP profile / dashboard parity"          "$PY" -c "
import json; from pathlib import Path
a=json.loads(Path('skills/mcp/data/mcp-profile-v3.1.json').read_text()); b=json.loads(Path('dashboard/public/data/mcp-profile-v3.1.json').read_text())
assert a==b and a['metadata']['framework_controls_total']==161 and len(a['controls'])==19"
# security.yml
if [ -n "${SEMGREP:-}" ]; then gate "semgrep .semgrep/security.yml" "$SEMGREP" scan --config .semgrep/security.yml --error --metrics=off --quiet .
else skip "semgrep" "set SEMGREP"; fi
if [ -n "${GITLEAKS:-}" ]; then gate "gitleaks (HEAD history, baseline)" "$GITLEAKS" git --redact --log-opts=HEAD --baseline-path .gitleaks-baseline.json .
else skip "gitleaks" "set GITLEAKS"; fi
# cli-release-qualification.yml
whl=$(ls "$OUT"/dist/*.whl 2>/dev/null | head -1)
if [ -n "$whl" ]; then
  rq=$(mktemp -d); python3 -m venv "$rq/v" >/dev/null
  gate "release: clean wheel install"          "$rq/v/bin/pip" install -q "$whl"
  ver=$("$PY" -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
  gate "release: check_release_installation"   "$rq/v/bin/python" -I scripts/check_release_installation.py --expected-version "$ver"
  gate "release: challenge offline workflow"   bash -c "cd \$(mktemp -d) && '$rq/v/bin/safe2' challenge quickstart 001 --output-dir s && '$rq/v/bin/safe2' challenge verify-bundle s && '$rq/v/bin/safe2' challenge validate 001"
else skip "release qualification" "no wheel built"; fi
echo "gates failed: $fails  (logs: $OUT)"
[ "$fails" -eq 0 ]
