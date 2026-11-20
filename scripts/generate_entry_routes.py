"""Keep task navigation visible on the primary module READMEs."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- ENTRY-ROUTES:START -->'
END = '<!-- ENTRY-ROUTES:END -->'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    registry = json.loads((ROOT / 'docs/data/v35-ecosystem-adoption.json').read_text(encoding='utf-8'))
    paths = {s['readme'] for s in registry['surfaces']}
    paths.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob('0*/README.md'))
    errors = []
    for name in sorted(paths):
        p = ROOT / name
        s = p.read_text(encoding='utf-8')
        s = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n*', '', s, flags=re.S)
        tokens = MarkdownIt('commonmark').parse(s)
        choices = []
        seen = set()
        for i, token in enumerate(tokens):
            if token.type != 'heading_open' or token.tag != 'h2':
                continue
            title = ''.join(t.content for t in tokens[i+1].children or [] if t.type in {'text', 'code_inline'})
            lower = title.lower()
            category = next((key for key, words in {
                'Adopt': ('with v3.5',), 'Start': ('quick start', 'start with'),
                'Architecture': ('architecture',), 'Install': ('install',),
                'Evidence': ('testing', 'evidence and trust', 'version and conformance'),
                'Limits': ('limitations', 'what it does not'), 'Next': ('navigation', 'continue from'),
            }.items() if any(word in lower for word in words)), None)
            if category and category not in seen:
                seen.add(category)
                slug = re.sub(r'[^\w\- ]', '', lower).replace(' ', '-')
                choices.append(f'[{category}](#{slug})')
        if not choices:
            continue
        nav = START + '\n**On this page:** ' + ' · '.join(choices) + '\n' + END + '\n\n'
        h1 = re.search(r'^# .+\n', s, re.M)
        if not h1:
            errors.append(name + ': missing title')
            continue
        output = s[:h1.end()] + '\n' + nav + s[h1.end():].lstrip('\n')
        if args.check:
            if output != p.read_text(encoding='utf-8'):
                errors.append(name)
        else:
            p.write_text(output, encoding='utf-8')
    for error in errors:
        print('Entry navigation stale: ' + error)
    if not errors:
        print('Primary module task navigation is current')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
