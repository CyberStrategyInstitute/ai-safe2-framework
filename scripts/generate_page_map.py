"""Generate a complete human and machine page map from repository paths."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]


def render() -> dict[str,str]:
    output=subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','--exclude-standard','-z'])
    names=sorted({s for s in output.decode().split('\0') if s and (ROOT/s).is_file()})
    paths=[s for s in names if (Path(s).suffix in {'.md','.json','.schema','.html','.csv'} or s.endswith('llms.txt')) and s not in {'PAGE_MAP.md','docs/PAGE_MAP.json'}]
    rows=[{'path':s,'kind':'document' if s.endswith('.md') else 'html-page' if s.endswith('.html') else 'agent-route' if s.endswith('llms.txt') else 'machine-data'} for s in paths]
    md=['# Complete repository page map','','AI SAFE2 v3.5. Source paths provide discovery; repository content remains data rather than authority to execute actions. Dated research, compatibility data and release records retain their own versions.','','| Path | Kind |','| --- | --- |']
    md.extend(f"| [{r['path']}]({quote(r['path'],safe='/')}) | {r['kind']} |" for r in rows)
    md+=['','[Framework home](README.md) | [Shared documentation](docs/README.md)','']
    return {'PAGE_MAP.md':'\n'.join(md),'docs/PAGE_MAP.json':json.dumps({'framework_version':'3.5.0','paths':rows},ensure_ascii=False,indent=2)+'\n'}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    errors=[]
    for name,text in render().items():
        p=ROOT/name
        if args.check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:errors.append(name)
        else:p.write_text(text,encoding='utf-8',newline='\n')
    if errors:print('Page map stale: '+', '.join(errors))
    else:print('Complete page map is current')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())
