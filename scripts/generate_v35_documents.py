"""Render the v3.5 normative projections and research decisions from their owners."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def documents() -> dict[str, str]:
    catalog = json.loads((ROOT / 'safe2/data/ai-safe2-controls-v3.5.json').read_text(encoding='utf-8'))
    decisions = json.loads((ROOT / 'safe2/data/framework-requirements-v3.5.json').read_text(encoding='utf-8'))['decisions']
    controls = catalog['pillar_controls'] + catalog['cross_pillar_controls']
    observations = {o['id']: o for o in json.loads((ROOT/'safe2/data/threat-observations-v3.5.json').read_text(encoding='utf-8'))['observations']}
    pages = {}
    text = ['# AI SAFE2 v3.5 control contracts', '', 'AI SAFE2 v3.5 normative requirements. Baseline v3.1 contains 161 controls. This revision retains those IDs and adds twelve controls, yielding 173. Existing component implementations retain their separately evidenced status. A requirement is an obligation on applicable deployments; source availability alone establishes no enforcement result.', '', 'Applicability must be recorded for the deployment, effect, actor and consequence. Each applicable child clause requires an identified enforcement or governance owner, test evidence, failure response and recovery procedure. Research-only clauses document unsettled measurements and do not impose a runtime threshold.', '', '| Control | Name | Change |', '| --- | --- | --- |']
    for c in controls:
        state = 'NEW' if c.get('version_added') == 'v3.5' else 'UPDATED' if c.get('requirements') else 'RETAINED'
        text.append(f"| [{c['id']}](#{c['id'].lower().replace('.','-')}) | {c['name']} | {state} |")
    for c in controls:
        cid=c['id']
        text += ['', f'<a id="{cid.lower().replace(".","-")}"></a>', '', f"## {cid} {c['name']}", '', c['description']]
        related = [d for d in decisions if d['control_id']==cid]
        for d in related:
            text += ['', f"### {d['review_id']} inherited requirement detail", '', d['rationale'], '', '**Source and research** '+d['source'], '', f"[Research decision](../{d['research_path']})", '']
            for cl in d['clauses']:
                modal = 'Research requirement' if cl['disposition']=='research' else 'Requirement'
                text.append(f"- **{cl['id']}** ({modal}) {cl['requirement']}")
            text += ['', '**Acceptance and failure analysis** '+d['validation'], '', 'On a failed applicable acceptance condition, record failed or unknown coverage, narrow the deployment authority to the demonstrated boundary, and assign corrective action and recovery to the named owner. An assessor must retain contrary results and unresolved effects.']
    text += ['', '[Framework home](../README.md) · [Machine catalog](../safe2/data/ai-safe2-controls-v3.5.json) · [Research index](../research/README.md)', '']
    pages['docs/CONTROLS-V3.5.md']='\n'.join(text)
    for d in decisions:
        parent=next(c for c in controls if c['id']==d['control_id'])
        note=['<!-- AI-SAFE2-UX:START -->', '[![AI SAFE² v3.5](https://img.shields.io/badge/AI_SAFE2-v3.5-F6921E)](../README.md)', '[![Research](https://img.shields.io/badge/Research-820F1A)](./README.md)', '[![Requirements](https://img.shields.io/badge/Requirements-808080)](../docs/CONTROLS-V3.5.md)', '[Framework Home](../README.md) | [Research Index](./README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md)', '<!-- AI-SAFE2-UX:END -->', '', f"# {parent['name']} | {d['review_id']}", '', '**Status** Source-derived design analysis, v3.5. The requirements below define the v3.5 framework. Independent effectiveness verification remains deployment-specific.', '', '## Question and source', '', d['source'], '', 'The source record preserves historical proposals, corrections and limitations. Study percentages and analyst scores require the original study denominator and deployment context before use as prevalence or effectiveness claims. The reviewed source inventory is in the [expansion review](../docs/FRAMEWORK-EVIDENCE-EXPANSION.md).', '', '## Placement and alternatives', '', d['rationale'], '', f"The primary owner is **{d['control_id']} {parent['name']}**. Its child clauses preserve this distinct failure mechanism. The competing design is a separate control or deployment profile. Separation is justified when ownership, applicability, enforcement or acceptance cannot be represented by this parent. Absorption requires this explicit detail, a linked acceptance case and a migration record.", '']
        note += ['## Supporting reported findings', '', d['source_link_interpretation'], '']
        for oid in d['supporting_observations']:
            observation=observations[oid]
            note += [f"### {oid} {observation['title']}", '',
                     '**Reported facts in the supplied review** '+observation['reported_facts'], '',
                     '**Source-assigned evidence** '+observation['source_assigned_evidence'], '',
                     '**Limits** '+observation['limitations'], '']
            note += [f'[Source reference {n}]({url})' for n,url in enumerate(observation['source_urls'],1)]
            note += ['']
        note += ['## Requirements and implementation consequences', '']
        note += [f"- **{c['id']}** {c['requirement']}" for c in d['clauses']]
        note += ['', '## Adversarial validation and contrary evidence', '', d['validation'], '', 'Include a legitimate-use control case, denied or unsafe conditions, missing evidence, unavailable dependencies, and the observed recovery outcome where applicable. Measure useful completion and false refusals alongside prevented effects. An existing implementation that demonstrably satisfies the same objective is contrary evidence to adding duplicate machinery. Preserve that result and revise the placement without deleting the underlying failure case.', '', '## Evidence and interpretation', '', 'Record actor/origin, entry surface, permitted authority, persistence, affected resource, effect, enforcement point and recovery. Separate disclosed vulnerability, laboratory demonstration, observed exploitation, and incident attribution. Source publication, event and fix dates retain distinct meanings. Deterministic decisions require specified inputs and policy; they do not establish a general safety guarantee.', '', '## Failure and recovery', '', 'The deployment owner records partial and unknown outcomes, contains the affected authority where warranted, preserves minimal reconstruction evidence, and revalidates after correction. Quantitative thresholds need declared units, population, uncertainty and policy ownership. Human-state or legal conclusions require their own validation and applicability review.', '', '<!-- AI-SAFE2-UX-FOOTER:START -->', '[Research Index](./README.md) | [Framework Home](../README.md) | [Cross-Pillar Governance](../00-cross-pillar/README.md) | [AISM](../AISM/README.md)', '<!-- AI-SAFE2-UX-FOOTER:END -->', '']
        pages[d['research_path']]='\n'.join(note)
    profiles={'HARNESS':['C02','C25'],'GATEWAY':['C01','C03','C26'],'EVAL':['C16','C27','C48'],'CUA':['C28','C40'],'FIN':['C29','C35'],'PHYSICAL':['C31','C34']}
    for name,keys in profiles.items():
        lines=[f'# CP.5.{name} | v3.5 profile','', 'This profile applies when the deployment includes this operating boundary. It inherits the linked core objectives and requires a recorded applicability decision. Profile requirements are excluded from the core control count. Implementations must identify which concrete paths enforce each obligation and retain explicit unsupported and untested routes.','']
        for d in decisions:
            if d['review_id'] in keys:
                lines += [f"## {d['control_id']} | {d['review_id']}", '',d['rationale'],'']+[f"- **{cl['id']}** {cl['requirement']}" for cl in d['clauses']]+['', '**Acceptance** '+d['validation'],'',f"[Research](../{d['research_path']})",'']
        lines += ['[Cross-Pillar Governance](README.md) | [Framework Home](../README.md) | [Full control contracts](../docs/CONTROLS-V3.5.md)','']
        pages[f'00-cross-pillar/cp5_{name.lower()}_v35.md']='\n'.join(lines)
    mcp=json.loads((ROOT/'skills/mcp/data/mcp-profile-v3.5.json').read_text(encoding='utf-8'))
    lines=['# CP.5.MCP v3.5 | current-condition and outcome requirements','','Profile requirements. The nineteen v3.1 IDs and protocol bindings are retained. Twelve distinct child clauses deepen the requirements; shared clauses can support more than one profile control. Apply core CP.11-CP.15, F3.6-F3.7 and A2.7-A2.9 wherever applicable.','']
    for c in mcp['controls']:
        lines += [f"## {c['id']} {c['name']}",'',c['description'],'']+[f"- **{cl['id']}** {cl['requirement']}" for cl in c['requirements']]
    lines += ['','[v3.1 compatibility specification](cp5_mcp_server_security.md) | [Cross-Pillar Governance](README.md) | [Framework Home](../README.md)','']
    pages['00-cross-pillar/cp5_mcp_v35.md']='\n'.join(lines)
    return pages


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    stale=[]
    for name,content in documents().items():
        content = content.replace("\u2013", "-").replace("\u2014", "-")
        p=ROOT/name
        if args.check:
            if not p.exists() or p.read_text(encoding='utf-8')!=content:stale.append(name)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(content,encoding='utf-8',newline='\n')
    if stale:
        print('Stale v3.5 projections: '+', '.join(stale))
        return 1
    print('v3.5 control, profile and research projections are current')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
