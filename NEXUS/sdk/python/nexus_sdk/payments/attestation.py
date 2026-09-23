"""Runtime Proof (`AttestationVerifier`) for CP.5.APAY.

Runtime measurements are assertions until a verifier checks freshness, a
verifier-issued challenge, a trusted signer, and the measured baseline. The
default verifier refuses all evidence. The HMAC verifier is a portable
reference/test mechanism, not a substitute for TDX/SNP/TPM verification.
"""
from __future__ import annotations

import hashlib
import hmac
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from nexus_sdk.payments.objects import RuntimeMeasurement, utcnow


@dataclass(frozen=True)
class AttestationResult:
    accepted: bool
    reason: str
    verifier: str


class AttestationVerifier(ABC):
    human_name = "Runtime Proof"
    technical_name = "AttestationVerifier"

    @abstractmethod
    def verify(self, measurement: RuntimeMeasurement, *, expected_baseline: Optional[str],
               now: Optional[datetime] = None) -> AttestationResult: ...


class NullAttestationVerifier(AttestationVerifier):
    """Fail-Closed Runtime Proof (`NullAttestationVerifier`)."""
    def verify(self, measurement: RuntimeMeasurement, *, expected_baseline: Optional[str],
               now: Optional[datetime] = None) -> AttestationResult:
        return AttestationResult(False, "no attestation verifier configured", type(self).__name__)


class HMACTestAttestationVerifier(AttestationVerifier):
    """Test Runtime Proof (`HMACTestAttestationVerifier`); never production."""
    def __init__(self, keys: dict[str, bytes], challenges: set[str]):
        self._keys = dict(keys)
        self._challenges = set(challenges)
        self._lock = threading.RLock()

    @staticmethod
    def message(measurement: RuntimeMeasurement) -> bytes:
        return "|".join((measurement.workload_id or "", measurement.baseline_digest(),
                         measurement.measured_at, measurement.verifier_challenge or "")).encode()

    def verify(self, measurement: RuntimeMeasurement, *, expected_baseline: Optional[str],
               now: Optional[datetime] = None) -> AttestationResult:
        if not measurement.is_fresh(now or utcnow()):
            return AttestationResult(False, "measurement stale", type(self).__name__)
        if not measurement.workload_id:
            return AttestationResult(False, "workload identity missing", type(self).__name__)
        with self._lock:
            if (not measurement.verifier_challenge
                    or measurement.verifier_challenge not in self._challenges):
                return AttestationResult(
                    False, "challenge absent, unknown, or already consumed", type(self).__name__
                )
            key = self._keys.get(measurement.attestation_signer or "")
            if not key or not measurement.attestation_evidence:
                return AttestationResult(
                    False, "untrusted signer or missing evidence", type(self).__name__
                )
            if expected_baseline and measurement.baseline_digest() != expected_baseline:
                return AttestationResult(False, "baseline mismatch", type(self).__name__)
            expected = hmac.new(key, self.message(measurement), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, measurement.attestation_evidence):
                return AttestationResult(False, "evidence signature invalid", type(self).__name__)
            self._challenges.remove(measurement.verifier_challenge)
        return AttestationResult(True, "verified", type(self).__name__)
