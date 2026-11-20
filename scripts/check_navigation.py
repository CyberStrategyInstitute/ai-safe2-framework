"""Validate primary navigation anchors, agent routes and adoption contracts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'scripts'))
from review_repository_surfaces import classification, names
PARSER = MarkdownIt('commonmark', {'html': True})


def anchors(path: Path) -> set[str]:
    text = path.read_text(encoding='utf-8-sig')
    result = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    seen: dict[str, int] = {}
    tokens = PARSER.parse(text)
    for i, token in enumerate(tokens):
        if token.type != 'heading_open':
            continue
        inline = tokens[i + 1]
        title = ''.join(t.content for t in inline.children or [] if t.type in {'text', 'code_inline'})
        slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        result.add(slug + (f'-{n}' if n else ''))
    return result


def main() -> int:
    manifest = json.loads((ROOT / 'ai-safe2.manifest.json').read_text(encoding='utf-8'))
    registry = json.loads((ROOT / 'docs/data/v35-ecosystem-adoption.json').read_text(encoding='utf-8'))
    errors = []
    if registry['framework_version'] != manifest['framework']['version']:
        errors.append('adoption_framework_version_mismatch')
    if len({s['id'] for s in registry['surfaces']}) != len(registry['surfaces']):
        errors.append('duplicate_adoption_surface')
    allowed = {'compatible-reference', 'partial-reference', 'scaffolding', 'implemented-bounded', 'contract-preview', 'guidance', 'mixed-reference', 'prospective'}
    paths = {'README.md', 'docs/README.md', 'docs/V35-ECOSYSTEM-ADOPTION.md', 'llms.txt'}
    for s in registry['surfaces']:
        paths.add(s['readme'])
        if s['status'] not in allowed:
            errors.append(s['id'] + ': unknown status')
        for key in ('readme', 'source', 'verification_path'):
            if not (ROOT / s[key]).exists():
                errors.append(s['id'] + ': missing ' + key)
        if '<!-- V35-ADOPTION:START -->' not in (ROOT / s['readme']).read_text(encoding='utf-8'):
            errors.append(s['id'] + ': missing adoption route')
    paths.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob('0*/README.md'))
    paths.update(n for n in names() if Path(n).name.lower()=='readme.md' and classification(n)[0] in {'current-topic-surface','current-entrypoint','separate-policy-material'})
    cache: dict[Path, set[str]] = {}
    for name in sorted(paths):
        p = ROOT / name
        for block in PARSER.parse(p.read_text(encoding='utf-8')):
            for token in block.children or []:
                target = token.attrGet('href') if token.type == 'link_open' else None
                if not target:
                    continue
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith('/'):
                    continue
                dest = (p.parent / unquote(parsed.path)).resolve() if parsed.path else p.resolve()
                if not dest.exists():
                    errors.append(f'{name}: missing {target}')
                elif parsed.fragment and dest.suffix in {'.md', '.txt'}:
                    if dest not in cache:
                        cache[dest] = anchors(dest)
                    if unquote(parsed.fragment) not in cache[dest]:
                        errors.append(f'{name}: unresolved anchor {target}')
    home = (ROOT / 'README.md').read_text(encoding='utf-8')
    for marker in ('# AI SAFE² Framework v3.5', 'assets/v35-adoption-map.svg', 'AGENTS.md', 'llms.txt', 'ai-safe2.manifest.json', '## Star History', '## Help improve the framework'):
        if marker not in home:
            errors.append('README.md: missing ' + marker)
    for error in sorted(set(errors)):
        print(error)
    if not errors:
        print('Primary navigation anchors, agent routes and component adoption contracts passed')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
