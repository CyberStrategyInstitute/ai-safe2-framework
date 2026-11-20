"""Check Markdown file targets without following external links or executing content."""
from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parents[1]


def main() -> int:
    names=set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0'))
    parser=MarkdownIt('commonmark');errors=[]
    for name in sorted(names):
        p=ROOT/name
        if p.suffix!='.md' or not p.is_file():continue
        for block in parser.parse(p.read_text(encoding='utf-8-sig')):
            for token in block.children or []:
                target=token.attrGet('href') if token.type=='link_open' else token.attrGet('src') if token.type=='image' else None
                if not target or target.startswith(('#','/')) or urlsplit(target).scheme:continue
                path=unquote(urlsplit(target).path)
                if path and not (p.parent/path).exists():errors.append(f'{name}: {target}')
    for error in errors:print(error)
    if not errors:print('Local Markdown file targets are valid')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())
