"""Generate an offline mapping explorer and source-family review index."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from safe2.framework import audit_registry, controls, data


def outputs():
    registry=data('rosetta-v3.5.json')
    payload={'registry':registry,'controls':list(controls().values()),'control_anchors':{cid:cid.lower().replace('.','-') for cid in controls()},'audit':audit_registry(registry)}
    serialized=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<',chr(92)+'u003c')
    html=(ROOT/'dashboard/rosetta-template.html').read_text(encoding='utf-8').replace('__DATA__',serialized)
    rows=['# Rosetta Stone source-family index','','[Framework home](../README.md) | [Mapping guide](ROSETTA-STONE-V35.md) | [Offline explorer source](../dashboard/rosetta.html) | [Canonical registry](../safe2/data/rosetta-v3.5.json)','','Choose your source family below. Open the explorer locally through `python -m http.server 8765 --bind 127.0.0.1` from a reviewed checkout, then visit `http://127.0.0.1:8765/dashboard/rosetta.html`. GitHub displays HTML source; Pages can render this explorer only after the relevant branch is deployed.','','Recorded relationships are historical/unreviewed until their source, applicability and evidence are validated. An empty result remains an explicit gap.','','| Source family | Recorded relationships | Status counts | Source verification |','| --- | --- | --- | --- |']
    for s in registry['sources']:
        rel=[r for r in registry['relationships'] if r['source_id']==s['id']]
        statuses=', '.join(f'{k}: {v}' for k,v in sorted(Counter(r['status'] for r in rel).items()))
        rows.append(f"| [{s['id']}](../dashboard/rosetta.html#source={s['id']}) · {s['title'].replace('|','/')} | {len(rel)} | {statuses or 'No relationships'} | {s.get('edition_status','unassessed')} |")
    rows+=['','For a source plus control, use `safe2 framework query --source NIST_AI_RMF --control P1.T1.1`. For a new control with no recovered mapping, retain that gap and review the source directly before adding a relationship.','','[Review all sixteen audit checks](ROSETTA-STONE-V35.md) | [Control contracts](CONTROLS-V3.5.md) | [Evidence request](../AISM/TECHNOLOGY-EVIDENCE-REQUEST.md)','']
    return {'dashboard/rosetta.html':html,'docs/ROSETTA-SOURCE-INDEX.md':'\n'.join(rows)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();errors=[]
    for name,text in outputs().items():
        path=ROOT/name
        if a.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=text:errors.append(name)
        else:path.write_text(text,encoding='utf-8')
    for name in errors:print('Rosetta projection stale: '+name)
    if not errors:print('Rosetta explorer, source index and canonical records are synchronized')
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
