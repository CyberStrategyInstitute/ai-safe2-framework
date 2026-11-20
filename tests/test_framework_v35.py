"""Regression cases for v3.5 contracts, recovery mappings and local effects."""
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime

import pytest
from click.testing import CliRunner

from safe2.authority_fixture import AuthorityFixture, approve
from safe2.cli import cli
from safe2.framework import audit_registry, controls, data, readiness

NOW = datetime(2026, 11, 19, tzinfo=UTC)


def evidence():
    return {'schema_version': 'safe2.deployment-readiness.v1', 'framework_version': '3.5.0',
            'system_id': 'synthetic', 'revision': 'abc', 'scope': 'local fixture',
            'required_controls': ['CP.12'], 'observations': [
                {'control_id': 'CP.12', 'revision': 'abc', 'scope': 'local fixture', 'result': 'pass',
                 'evidence_id': 'private-reference', 'independence': 'independent',
                 'observed_at': '2026-11-18T00:00:00Z', 'valid_until': '2026-11-20T00:00:00Z'}]}


def test_catalog_and_legacy_baseline():
    current = controls()
    assert len(current) == 173
    assert {f'CP.{n}' for n in range(1, 16)} <= set(current)
    assert len(current['CP.12']['requirements']) == 6
    legacy = data('ai-safe2-controls-v3.0.json')
    assert len(legacy['pillar_controls']) + len(legacy['cross_pillar_controls']) == 161
    assert len(data('framework-requirements-v3.5.json')['decisions']) == 52


@pytest.mark.parametrize('field,value', [('result', 'unknown'), ('result', 'fail'), ('independence', 'self-reported'),
                                        ('scope', 'wrong'), ('revision', 'old'),
                                        ('valid_until', '2026-11-18T00:00:00Z'),
                                        ('observed_at', '2026-11-20T00:00:00Z')])
def test_readiness_holds_incomplete_or_misbound_observations(field, value):
    source = evidence()
    source['observations'][0][field] = value
    assert readiness(source, NOW)['result'] == 'hold'


def test_readiness_is_not_authorization_and_conflicts_hold():
    source = evidence()
    result = readiness(source, NOW)
    assert result['result'] == 'ready-for-human-evidence-review'
    assert result['authorization_granted'] is False
    source['observations'].append(deepcopy(source['observations'][0]))
    assert readiness(source, NOW)['result'] == 'hold'
    source['observations'] = []
    assert readiness(source, NOW)['result'] == 'hold'


def test_readiness_rejects_wrong_contract():
    source = evidence()
    source['required_controls'] = []
    with pytest.raises(ValueError, match='invalid_readiness_contract'):
        readiness(source, NOW)


def test_recovery_audit_never_promotes_historical_tags():
    result = audit_registry(data('rosetta-v3.5.json'))
    assert result['errors'] == []
    assert result['recorded_relationships'] == 1202
    assert result['approved_relationships'] == 0
    assert result['verified_external_coverage'] is None
    assert result['checks']['RS02']['status'] == 'unassessed'
    assert result['checks']['RS09']['status'] == 'pass'


def test_mapping_promotion_requires_reviewed_source():
    registry = data('rosetta-v3.5.json')
    registry['relationships'][0]['status'] = 'approved'
    result = audit_registry(registry)
    assert result['checks']['RS02']['status'] == 'fail'
    assert result['checks']['RS12']['status'] == 'fail'


def test_cli_queries_exact_ids_and_strict_mapping_holds():
    runner = CliRunner()
    result = runner.invoke(cli, ['framework', 'query', '--control', 'CP.12'])
    assert result.exit_code == 0
    assert json.loads(result.output)['controls'][0]['id'] == 'CP.12'
    assert runner.invoke(cli, ['framework', 'query', '--control', 'CP-TL']).exit_code != 0
    assert runner.invoke(cli, ['framework', 'audit', '--strict']).exit_code == 1


@pytest.fixture
def fixture(tmp_path):
    key = b'synthetic-fixture-key-only-32-bytes'
    runtime = AuthorityFixture(tmp_path/'fixture.sqlite', key)
    runtime.grant(principal='root', task='task', environment='test', resource='record', purpose='fixture', ceiling=2, expires=1000)
    runtime.grant(principal='child', parent='root', task='task', environment='test', resource='record', purpose='fixture', ceiling=2, expires=900)
    runtime.resource('record', 'initial')
    return runtime, key


def action(**kwargs):
    return dict(key='operation-1', principal='child', task='task', environment='test', resource='record',
                purpose='fixture', units=1, expected_version=0, value='changed', **kwargs)


def execute(runtime, key, request, nonce='nonce'):
    approval = approve(request, principal=request['principal'], expires=500, nonce=nonce, key=key)
    return runtime.execute(request, approval, now=100)


def test_effect_verified_and_duplicate_not_reexecuted(fixture):
    runtime, key = fixture
    request = action()
    first = execute(runtime, key, request)
    assert first['effect'] == 'BIND'
    assert execute(runtime, key, request) == first
    with runtime.connect() as db:
        assert db.execute('SELECT version FROM resources').fetchone()[0] == 1
        assert db.execute("SELECT spent FROM grants WHERE principal='root'").fetchone()[0] == 1


@pytest.mark.parametrize('field,value', [('value','substituted'), ('resource','other'), ('environment','production'), ('units',2)])
def test_approval_is_bound_to_exact_action(fixture, field, value):
    runtime, key = fixture
    request = action()
    approval = approve(request, principal='child', expires=500, nonce='nonce', key=key)
    request[field] = value
    assert runtime.execute(request, approval, now=100)['effect'] == 'NO_BIND'


def test_environment_and_stale_resource_are_checked_after_approval(fixture):
    runtime,key=fixture
    request=action();request['environment']='production'
    assert execute(runtime,key,request)['reason']=='invalid_current_authority'
    request=action();request['expected_version']=1
    assert execute(runtime,key,request)['reason']=='stale_resource_state'


@pytest.mark.parametrize('state,decision', [('pause','PAUSE'),('unknown','ESCALATE'),('conflicting','ESCALATE')])
def test_current_condition_and_root_revocation(fixture,state,decision):
    runtime,key=fixture
    runtime.condition('root',state)
    result=execute(runtime,key,action())
    assert result['decision']==decision and result['effect']=='NO_BIND'
    runtime.revoke('root')
    assert execute(runtime,key,action())['reason']=='invalid_current_authority'


def test_concurrent_children_cannot_overspend_root(fixture):
    runtime,key=fixture
    with runtime.connect() as db:
        db.execute("UPDATE grants SET ceiling=1 WHERE principal='root'")
    requests=[action() for _ in range(2)]
    requests[1]['key']='operation-2'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda pair:execute(runtime,key,pair[1],str(pair[0])),enumerate(requests)))
    assert sum(r['effect']=='BIND' for r in results)==1
    assert any(r.get('reason')=='aggregate_ceiling' for r in results)


def test_delegation_cannot_widen_and_idempotency_conflict(fixture):
    runtime,key=fixture
    with pytest.raises(ValueError,match='delegation_widens'):
        runtime.grant(principal='wide',parent='root',task='task',environment='production',resource='record',purpose='fixture',ceiling=2,expires=900)
    request=action();execute(runtime,key,request)
    request['value']='different'
    assert execute(runtime,key,request,'nonce-2')['reason']=='idempotency_key_conflict'


def test_approval_expiry_and_invalid_quantity(fixture):
    runtime,key=fixture
    request=action()
    approval=approve(request,principal='child',expires=99,nonce='nonce',key=key)
    assert runtime.execute(request,approval,now=100)['effect']=='NO_BIND'
    request['units']=True
    with pytest.raises(ValueError,match='invalid_action_quantity'):
        runtime.execute(request,approval,now=100)


def test_malformed_mapping_input_fails_closed():
    with pytest.raises(ValueError, match="invalid_rosetta_contract"):
        audit_registry({"sources": "invalid", "relationships": []})


def test_reviewed_mapping_checks_source_revision_and_freshness():
    registry = data('rosetta-v3.5.json')
    relation = registry['relationships'][0]
    source = next(s for s in registry['sources'] if s['id'] == relation['source_id'])
    source.update(publisher='synthetic publisher', edition='test edition', publication_status='test',
                  canonical_url='https://example.test/source', locator_inventory=['test-unit'], revision='revision-1')
    relation.update(status='approved', relationship='supports', external_reference='test-unit',
                    role='test role', scope='test scope', exclusions='explicit test exclusions',
                    basis='direct-source-review', claim_kind='requirement-only',
                    reviewed_at='2026-11-18T00:00:00Z', valid_until='2026-11-20T00:00:00Z',
                    reviewer='test reviewer', revisit_trigger='source change', source_revision='revision-1',
                    source_verification='verified', reuse_scope='test scope')
    result = audit_registry(registry, NOW)
    assert result['checks']['RS11']['failures'] == 0
    assert result['checks']['RS09']['status'] == 'pass'
    source['revision'] = 'revision-2'
    assert audit_registry(registry, NOW)['checks']['RS11']['failures'] == 1
    source['revision'] = 'revision-1'
    relation['valid_until'] = '2026-11-18T00:00:00Z'
    assert audit_registry(registry, NOW)['checks']['RS11']['failures'] == 1
