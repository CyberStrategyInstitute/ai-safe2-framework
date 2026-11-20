"""Versioned framework lookup, mapping integrity and scoped readiness evidence."""
from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from importlib.resources import files

from jsonschema import Draft202012Validator, FormatChecker


def data(name: str) -> dict:
    return json.loads(files('safe2.data').joinpath(name).read_text(encoding='utf-8'))


def controls() -> dict[str, dict]:
    catalog = data('ai-safe2-controls-v3.5.json')
    return {c['id']: c for c in catalog['pillar_controls'] + catalog['cross_pillar_controls']}


def query(control_id: str | None = None, source_id: str | None = None) -> dict:
    catalog = controls()
    registry = data('rosetta-v3.5.json')
    if control_id is not None and control_id not in catalog:
        raise ValueError('unknown_or_ambiguous_control_id')
    if source_id is not None and source_id not in {s['id'] for s in registry['sources']}:
        raise ValueError('unknown_source_id')
    relationships = [r for r in registry['relationships']
                     if (control_id is None or control_id in r['control_ids'])
                     and (source_id is None or source_id == r['source_id'])]
    selected = {control_id} if control_id else {c for r in relationships for c in r['control_ids']}
    if not control_id and not source_id:
        selected = set(catalog)
    return {'framework_version': '3.5.0', 'release_status': 'current',
            'controls': [catalog[c] for c in sorted(selected) if c in catalog],
            'relationships': relationships,
            'interpretation': 'Recorded relationships remain attributed and unreviewed until their exact source and applicability are validated.'}


def audit_registry(registry: dict, now: datetime | None = None) -> dict:
    """Check record integrity without inferring external compliance coverage."""
    shape = {
        'type': 'object', 'required': ['sources', 'relationships', 'historical_control_tag_rows', 'historical_crosswalk_cells'],
        'properties': {
            'sources': {'type': 'array', 'items': {'type': 'object', 'required': ['id'], 'properties': {
                'id': {'type': 'string'}, 'locator_inventory': {'type': 'array', 'items': {'type': 'string'}},
                'publisher': {'type': 'string'}, 'edition': {'type': 'string'}, 'canonical_url': {'type': 'string'},
                'publication_status': {'type': 'string'}}}},
            'relationships': {'type': 'array', 'items': {'type': 'object',
                'required': ['id', 'source_id', 'control_ids', 'relationship', 'status'],
                'properties': {'id': {'type': 'string'}, 'source_id': {'type': 'string'},
                    'control_ids': {'type': 'array', 'items': {'type': 'string'}},
                    'relationship': {'type': 'string'}, 'status': {'type': 'string'},
                    'external_reference': {'type': ['string', 'null']}, 'evidence': {'type': 'array'}}}},
            'historical_control_tag_rows': {'type': 'integer', 'minimum': 0},
            'historical_crosswalk_cells': {'type': 'integer', 'minimum': 0}}}
    if list(Draft202012Validator(shape).iter_errors(registry)):
        raise ValueError('invalid_rosetta_contract')
    catalog = controls()
    sources = registry.get('sources', [])
    relations = registry.get('relationships', [])
    source_ids = [s.get('id') for s in sources]
    relation_ids = [r.get('id') for r in relations]
    errors = []
    if None in source_ids or len(set(source_ids)) != len(source_ids):
        errors.append('duplicate_or_missing_source_id')
    if None in relation_ids or len(set(relation_ids)) != len(relation_ids):
        errors.append('duplicate_or_missing_relationship_id')
    allowed_statuses = {'historical-unreviewed', 'unassessed', 'approved', 'disputed', 'superseded', 'not-applicable'}
    checks = {f'RS{i:02d}': {'status': 'pass', 'unassessed': 0, 'failures': 0} for i in range(1, 17)}

    def record(code: str, condition: bool, approved: bool) -> None:
        if condition:
            return
        key = 'failures' if approved else 'unassessed'
        checks[code][key] += 1
        checks[code]['status'] = 'fail' if checks[code]['failures'] else 'unassessed'

    by_source = {s.get('id'): s for s in sources}
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError('timezone_required')
    for relation in relations:
        approved = relation.get('status') == 'approved'
        internal = relation.get('relationship') == 'internal-dependency'
        source = by_source.get(relation.get('source_id'), {})
        if not source and not internal:
            errors.append('relationship_source_missing')
        record('RS01', internal or all(source.get(k) for k in ('publisher', 'edition', 'canonical_url', 'publication_status')), approved)
        record('RS02', internal or relation.get('external_reference') in source.get('locator_inventory', []), approved)
        record('RS03', bool(relation.get('control_ids')) and all(c in catalog for c in relation['control_ids']), approved)
        record('RS04', relation.get('relationship') in {'supports', 'partial', 'addresses', 'contradicts', 'internal-dependency'} and bool(relation.get('rationale')), approved)
        record('RS05', internal or all(relation.get(k) for k in ('role', 'scope', 'exclusions')), approved)
        record('RS06', internal or relation.get('basis') == 'direct-source-review', approved)
        evidence = relation.get('evidence', [])
        evidence_valid = bool(evidence) and all(isinstance(e, dict) and all(e.get(k) for k in ('id', 'revision', 'scope', 'result')) for e in evidence)
        record('RS07', relation.get('claim_kind') == 'requirement-only' or evidence_valid, approved)
        if relation.get('status') not in allowed_statuses:
            errors.append('invalid_relationship_status')
            record('RS08', False, True)
        current_review = False
        if all(relation.get(k) for k in ('reviewed_at', 'valid_until', 'reviewer', 'revisit_trigger', 'source_revision')):
            try:
                reviewed_at = datetime.fromisoformat(relation['reviewed_at'])
                valid_until = datetime.fromisoformat(relation['valid_until'])
                current_review = (reviewed_at.tzinfo is not None and valid_until.tzinfo is not None
                                  and reviewed_at <= now < valid_until
                                  and relation['source_revision'] == source.get('revision'))
            except (ValueError, TypeError):
                current_review = False
        record('RS11', current_review, approved)
        record('RS12', not approved or relation.get('source_verification') == 'verified', approved)
        record('RS13', bool(relation.get('reuse_scope')), approved)
        record('RS14', not relation.get('unresolved_conflicts'), approved)
        record('RS16', all(catalog.get(c, {}).get('description') for c in relation.get('control_ids', [])), approved)
    # Counts describe the recovered record set, not a denominator of obligations.
    counts = Counter('tag' if r['id'].startswith('RS-TAG-') else 'cell' if r['id'].startswith('RS-CELL-') else 'other' for r in relations)
    record('RS09', counts['tag'] == registry.get('historical_control_tag_rows') and counts['cell'] == registry.get('historical_crosswalk_cells'), True)
    # Both query directions use these exact records; mirrors are checked by repository CI.
    record('RS10', len(set(relation_ids)) == len(relation_ids), True)
    checks['RS15'] = {'status': 'requires-distribution-check', 'unassessed': 1, 'failures': 0}
    return {'framework_version': '3.5.0', 'errors': sorted(set(errors)), 'checks': checks,
            'approved_relationships': sum(r.get('status') == 'approved' for r in relations),
            'recorded_relationships': len(relations), 'verified_external_coverage': None,
            'interpretation': 'Structural checks and recorded mappings do not establish regulatory compliance.'}


def readiness(source: dict, now: datetime | None = None) -> dict:
    schema = data('deployment-readiness-v1.schema.json')
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(source))
    if errors:
        raise ValueError('invalid_readiness_contract')
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError('timezone_required')
    known = controls()
    findings = []
    for cid in source['required_controls']:
        observations = [o for o in source['observations'] if o['control_id'] == cid]
        reason = None
        if cid not in known:
            reason = 'unknown_control'
        elif len(observations) != 1:
            reason = 'missing_or_conflicting_observations'
        else:
            o = observations[0]
            observed = datetime.fromisoformat(o['observed_at'])
            expires = datetime.fromisoformat(o['valid_until'])
            if observed > now or expires <= now or expires <= observed:
                reason = 'stale_or_invalid_observation_time'
            elif o['revision'] != source['revision'] or o['scope'] != source['scope']:
                reason = 'revision_or_scope_mismatch'
            elif o['result'] != 'pass' or o['independence'] != 'independent':
                reason = 'required_evidence_not_independent_pass'
        findings.append({'control_id': cid, 'status': 'hold' if reason else 'evidence-present', 'reason': reason})
    return {'schema_version': 'safe2.deployment-readiness-result.v1', 'framework_version': '3.5.0',
            'system_id': source['system_id'], 'revision': source['revision'], 'scope': source['scope'],
            'result': 'hold' if any(f['reason'] for f in findings) else 'ready-for-human-evidence-review',
            'authorization_granted': False, 'findings': findings,
            'evidence_boundary': 'Input observations and independence are declarations. This evaluator checks completeness, scope and freshness; it does not authenticate an external observer or authorize deployment.'}
