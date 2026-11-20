"""Bounded SQLite effect fixture for v3.5 authority and retry requirements.

The database and approval key belong to the trusted fixture operator. Effects are
limited to the local synthetic resource table in the same transaction as grants,
budgets and receipts. This module makes no remote-transaction guarantee.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def digest(action: dict) -> str:
    return hashlib.sha256(json.dumps(action, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def approve(action: dict, *, principal: str, expires: int, nonce: str, key: bytes) -> dict:
    """Run on the trusted approval side after authenticating the human decision."""
    payload = {'action_digest': digest(action), 'principal': principal, 'expires': expires, 'nonce': nonce}
    signature = hmac.new(key, digest(payload).encode(), hashlib.sha256).hexdigest()
    return {**payload, 'signature': signature}


class AuthorityFixture:
    """Commit only local synthetic effects through a serialized authority check."""

    def __init__(self, path: Path, key: bytes):
        if len(key) < 32:
            raise ValueError('approval_key_requires_32_bytes')
        self.path = path
        self.key = key
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS grants (
                    principal TEXT PRIMARY KEY, parent TEXT, task TEXT NOT NULL,
                    environment TEXT NOT NULL, resource TEXT NOT NULL, purpose TEXT NOT NULL,
                    ceiling INTEGER NOT NULL, spent INTEGER NOT NULL DEFAULT 0,
                    expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
                    condition TEXT NOT NULL DEFAULT 'ready');
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY, value TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS receipts (
                    key TEXT PRIMARY KEY, digest TEXT NOT NULL, result TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS approvals (nonce TEXT PRIMARY KEY);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def grant(self, *, principal: str, task: str, environment: str, resource: str,
              purpose: str, ceiling: int, expires: int, parent: str | None = None) -> None:
        """Trusted operator configuration, outside the acting agent's interface."""
        if type(ceiling) is not int or not 0 <= ceiling <= 2**63 - 1:
            raise ValueError('invalid_ceiling')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if parent:
                p = db.execute('SELECT * FROM grants WHERE principal=?', (parent,)).fetchone()
                if not p or any(p[k] != v for k, v in {'task': task, 'environment': environment, 'resource': resource, 'purpose': purpose}.items()) or ceiling > p['ceiling'] or expires > p['expires'] or p['revoked']:
                    raise ValueError('delegation_widens_or_lacks_authority')
            db.execute('INSERT INTO grants(principal,parent,task,environment,resource,purpose,ceiling,expires) VALUES(?,?,?,?,?,?,?,?)',
                       (principal, parent, task, environment, resource, purpose, ceiling, expires))

    def resource(self, resource: str, value: str) -> None:
        with self.connect() as db:
            db.execute('INSERT INTO resources(id,value) VALUES(?,?)', (resource, value))

    def revoke(self, principal: str) -> None:
        with self.connect() as db:
            db.execute('UPDATE grants SET revoked=1 WHERE principal=?', (principal,))

    def condition(self, principal: str, state: str) -> None:
        if state not in {'ready', 'pause', 'unknown', 'conflicting'}:
            raise ValueError('invalid_condition')
        with self.connect() as db:
            db.execute('UPDATE grants SET condition=? WHERE principal=?', (state, principal))

    def execute(self, action: dict, approval: dict, *, now: int | None = None) -> dict[str, Any]:
        required = {'key', 'principal', 'task', 'environment', 'resource', 'purpose', 'units', 'expected_version', 'value'}
        if set(action) != required or any(not isinstance(action[k], str) or not action[k] for k in required - {'units', 'expected_version'}):
            raise ValueError('invalid_action_contract')
        if type(action['units']) is not int or not 0 < action['units'] <= 2**63 - 1 or type(action['expected_version']) is not int or action['expected_version'] < 0:
            raise ValueError('invalid_action_quantity')
        now = int(time.time()) if now is None else now
        payload = {k: approval.get(k) for k in ('action_digest', 'principal', 'expires', 'nonce')}
        expected = hmac.new(self.key, digest(payload).encode(), hashlib.sha256).hexdigest()
        if not isinstance(approval.get('signature'), str) or not hmac.compare_digest(expected, approval['signature']):
            return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'invalid_approval_signature'}
        if payload['principal'] != action['principal'] or payload['action_digest'] != digest(action) or type(payload['expires']) is not int or payload['expires'] <= now or not isinstance(payload['nonce'], str) or not payload['nonce']:
            return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'approval_scope_or_expiry'}
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            chain = []
            current = action['principal']
            while current:
                if current in {g['principal'] for g in chain} or len(chain) >= 64:
                    return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'invalid_lineage'}
                grant = db.execute('SELECT * FROM grants WHERE principal=?', (current,)).fetchone()
                if not grant or grant['revoked'] or grant['expires'] <= now or any(grant[k] != action[k] for k in ('task', 'environment', 'resource', 'purpose')):
                    return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'invalid_current_authority'}
                if grant['condition'] != 'ready':
                    return {'decision': 'PAUSE' if grant['condition'] == 'pause' else 'ESCALATE', 'effect': 'NO_BIND', 'reason': 'current_condition'}
                chain.append(grant)
                current = grant['parent']
            prior = db.execute('SELECT * FROM receipts WHERE key=?', (action['key'],)).fetchone()
            if prior:
                if prior['digest'] != digest(action):
                    return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'idempotency_key_conflict'}
                return json.loads(prior['result'])
            if db.execute('SELECT nonce FROM approvals WHERE nonce=?', (payload['nonce'],)).fetchone():
                return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'approval_replay'}
            if any(g['spent'] + action['units'] > g['ceiling'] for g in chain):
                return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'aggregate_ceiling'}
            resource = db.execute('SELECT * FROM resources WHERE id=?', (action['resource'],)).fetchone()
            if not resource or resource['version'] != action['expected_version']:
                return {'decision': 'REFUSE', 'effect': 'NO_BIND', 'reason': 'stale_resource_state'}
            db.execute('UPDATE resources SET value=?,version=version+1 WHERE id=?', (action['value'], action['resource']))
            for grant in chain:
                db.execute('UPDATE grants SET spent=spent+? WHERE principal=?', (action['units'], grant['principal']))
            db.execute('INSERT INTO approvals(nonce) VALUES(?)', (payload['nonce'],))
            observed = db.execute('SELECT value,version FROM resources WHERE id=?', (action['resource'],)).fetchone()
            if observed['value'] != action['value']:
                raise RuntimeError('postcondition_failed')
            result = {'decision': 'ALLOW', 'effect': 'BIND', 'observed_version': observed['version'], 'scope': 'local-synthetic-resource', 'independence': 'separate-db-observation-same-fixture'}
            db.execute('INSERT INTO receipts(key,digest,result) VALUES(?,?,?)', (action['key'], digest(action), json.dumps(result)))
            return result
