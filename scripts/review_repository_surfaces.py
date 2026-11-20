"""Account for every README, HTML page and root file; validate local HTML routes."""
from __future__ import annotations
import argparse
import csv
import io
import json
import re
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]


def names():
    return sorted({n for n in subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0') if n and (ROOT/n).is_file()})


def classification(name):
    if name.startswith(('tests/','test/')):return 'test-fixture','Preserve test meaning; never add operating instructions.'
    if name.startswith(('docs/assessments/','challenges/001-','releases/','NEXUS/integrations/legacy-')) or name=='examples/openclaw/gateway-release-v3.0.html':return 'historical-or-frozen','Retain evidence/component/protocol identity; discover through current indexes.'
    if name=='dashboard/rosetta-template.html':return 'generator-template','Internal HTML template; generated explorer is the user entry point.'
    if name.startswith('FORGE-Act/'):return 'separate-policy-material','Retain policy content and status; shared navigation adds no legislative validation.'
    if '/' not in name:
        if name.lower() in {'readme.md','llms.txt','agents.md','integrations.md','ai-safe2.manifest.json'}:return 'current-entrypoint','Current framework routes, status and contracts.'
        return 'root-owning-source','Retain owning license, contract, component or configuration semantics; update only when affected.'
    return 'current-topic-surface','Current routes and explicit component/evidence boundaries; implementation claims remain scoped.'


class HTML(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if tag=='a' and a.get('name'):self.ids.add(a['name'])
        for key in ('href','src'):
            if a.get(key):self.links.append(a[key])


def outputs():
    allnames=names();rows=[];errors=[];cache={}
    for name in allnames:
        p=ROOT/name
        kind='readme' if p.name.lower()=='readme.md' else 'html' if p.suffix=='.html' else 'root-file' if '/' not in name else None
        if not kind:continue
        role,why=classification(name);raw=p.read_text(encoding='utf-8-sig',errors='replace') if p.suffix in {'.md','.txt','.html','.json'} else ''
        if kind=='readme' and role=='current-topic-surface' and '<!-- REPOSITORY-ROUTES:START -->' not in raw:
            errors.append(name+': missing shared route rail')
        if kind=='html':
            parser=HTML();parser.feed(raw)
            for target in parser.links:
                u=urlsplit(target)
                if u.scheme or target.startswith(('/','//')) or target=='#':continue
                dest=(p.parent/unquote(u.path)).resolve() if u.path else p.resolve()
                if not dest.exists():errors.append(name+': missing '+target)
                elif u.fragment and dest.suffix=='.html' and name!='dashboard/rosetta-template.html':
                    # Explorer fragments encode query filters rather than element IDs.
                    if '=' in u.fragment:continue
                    if dest not in cache:
                        h=HTML();h.feed(dest.read_text(encoding='utf-8',errors='replace'));cache[dest]=h.ids
                    if unquote(u.fragment) not in cache[dest]:errors.append(name+': missing HTML anchor '+target)
        rows.append({'path':name,'kind':kind,'disposition':role,'reason':why})
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=['path','kind','disposition','reason'],lineterminator='\n');w.writeheader();w.writerows(rows)
    counts=Counter(r['kind'] for r in rows);roles=Counter(r['disposition'] for r in rows)
    md=['# Repository surface review for v3.5','','[Framework home](../README.md) | [Full disposition CSV](data/repository-surface-review-v35.csv) | [Adoption guide](V35-ECOSYSTEM-ADOPTION.md) | [Page map](../PAGE_MAP.md)','','## Scope and interpretation','',f"Inventory: **{counts['readme']} README files, {counts['html']} HTML files and {counts['root-file']} other root files**. README/HTML counts are distinct categories; a root README is counted as a README. This is structural/documentation review, not runtime conformance or independent incident verification.",'','Every surfaced path has a disposition. Current topic READMEs share a navigation rail; module-specific headings, quickstarts and evidence boundaries remain local. Frozen challenges, dated assessments, release records, adversarial fixtures and separate policy material retain their meanings. Uniform navigation does not require identical bodies or images on fixtures.','','| Disposition | Paths |','| --- | --- |']
    md += [f'| {k} | {v} |' for k,v in sorted(roles.items())]
    md += ['','## Root files','','Root licenses, schemas, build configuration, lock files and component contracts are retained when their owning semantics are unchanged. A framework update does not justify rewriting every root file. The CSV enumerates each root path rather than calling untouched contracts updated.','','## HTML and guide decisions','','The control dashboard and generated Rosetta explorer are current source projections. The Claude Code HTML guide retains version-specific feature/incident context with an explicit revalidation notice. FORGE policy pages receive shared navigation without changing political content. The Gateway v3.0 release HTML remains historical. The Rosetta template is an internal generator input.','','Added guides: [v3.5 adoption and validation](../guides/V35-ADOPTION-AND-VALIDATION.md), [mapping validation](ROSETTA-STONE-V35.md), [source-family index](ROSETTA-SOURCE-INDEX.md), and [ecosystem adoption](V35-ECOSYSTEM-ADOPTION.md). Existing stack hardening/troubleshooting guides remain discoverable. No historical guide is deleted to obtain version uniformity.','','## Review passes and path checks','','1. Inventory all tracked/current README, HTML and root surfaces; classify historical, fixture, policy, generator and owning-source exceptions.','2. Inspect current framework counts, catalog selection, guide/index routes, component boundaries and visual entry points.','3. Validate local Markdown files, primary anchors, HTML file/anchor links, source/control/child-clause projections and generated freshness.','4. Exercise human and agent journeys through source mapping, current control requirements, research, implementation acceptance and version boundaries. Browser observations and executed test results are recorded in the PR description for the reviewed head.','','Passing route checks establish structural navigation. They do not verify external URLs, the substantive truth of mapping claims, deployment conformance, or every interaction on every historic page.','']
    return {'docs/data/repository-surface-review-v35.csv':out.getvalue(),'docs/REPOSITORY-SURFACE-REVIEW-V35.md':'\n'.join(md)},errors


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();result,errors=outputs()
    for name,text in result.items():
        path=ROOT/name
        if a.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=text:errors.append('Surface inventory stale: '+name)
        else:path.write_text(text,encoding='utf-8')
    for error in sorted(set(errors)):print(error)
    if not errors:print('All README, HTML and root surfaces have dispositions; local HTML routes passed')
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
