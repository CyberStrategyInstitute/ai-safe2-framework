"""Keep skill-version acceptance bound to the declared field."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('version,expected', [('v3.1', True), ('AI SAFE² v3.5', True), ('v0.0', False)])
def test_skill_card_declared_version(tmp_path, version, expected):
    fields = ['Skill Name', 'Framework Version', 'Owner', 'Purpose', 'Network Access',
              'Credential Access', 'Execution Capability', 'Data Persistence', 'Review Status']
    values = {'Framework Version': version, 'Purpose': 'A v3.5 mention cannot replace the declared version.'}
    card = tmp_path / 'SKILL-CARD.md'
    card.write_text('\n'.join(f'**{field}:** {values.get(field, "Declared")}' for field in fields), encoding='utf-8')
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_skill_card.py'), str(card), '--json'], capture_output=True, text=True)
    assert json.loads(result.stdout)['valid'] is expected
    assert result.returncode == (0 if expected else 1)
