"""Keep v3.5 requirements identified as the framework version across projections."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    errors=[]
    manifest=json.loads((ROOT/'ai-safe2.manifest.json').read_text(encoding='utf-8'))
    if manifest['framework']['version']!='3.5.0' or manifest['framework']['release_status']!='current':
        errors.append('Framework version/status mismatch')
    for name in ['safe2/data/ai-safe2-controls-v3.5.json','skills/mcp/data/ai-safe2-controls-v3.5.json','safe2/data/mcp-profile-v3.5.json','skills/mcp/data/mcp-profile-v3.5.json','dashboard/public/data/mcp-profile-v3.5.json']:
        d=json.loads((ROOT/name).read_text(encoding='utf-8'))
        if d['metadata']['release_status']!='current':errors.append(name+': stale framework status')
    for name in ['README.md','releases/AI-SAFE2-v3.5.0.md','docs/CONTROLS-V3.5.md','llms.txt','dashboard/rosetta-template.html']:
        text=(ROOT/name).read_text(encoding='utf-8').lower()
        if any(x in text for x in ['v3.5 candidate','v3.5 source candidate','v3.5_candidate','3.5.0--candidate']):errors.append(name+': stale framework label')
    if '| AI SAFE² Framework | 3.5.x | Current |' not in (ROOT/'SECURITY.md').read_text(encoding='utf-8'):
        errors.append('Security support matrix does not name v3.5')
    for e in errors:print(e)
    if not errors:print('AI SAFE2 v3.5 release identity is consistent')
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
