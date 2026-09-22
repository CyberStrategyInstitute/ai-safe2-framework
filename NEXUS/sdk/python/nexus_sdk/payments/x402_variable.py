"""SafePay Variable and SafePay Escrow x402 v2 profiles."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum

from nexus_sdk.payments.adapters import (
    BindingDecision, BindingResult, X402AuthoritativeVerifier,
    X402V2ExactEVMUSDCAuthoritativeBinding,
)
from nexus_sdk.payments.objects import AssuranceLevel, SettlementFinality


class EscrowPhase(str, Enum):
    NEW = "new"
    DEPOSITED = "deposited"
    CLOSED = "closed"


@dataclass(frozen=True)
class VariableCharge:
    ceiling: int
    actual: int

    def validate(self) -> list[str]:
        if self.ceiling < 0 or self.actual < 0:
            return ["amounts must be non-negative atomic-unit integers"]
        if self.actual > self.ceiling:
            return ["actual settlement exceeds signed ceiling"]
        return []


class X402V2UptoBinding(X402V2ExactEVMUSDCAuthoritativeBinding):
    """SafePay Variable (`X402V2UptoBinding`): EVM upto/authorization."""

    human_name = "SafePay Variable"
    technical_name = "X402V2UptoBinding"
    scheme = "upto"

    def _charge(self, payload: dict) -> tuple[VariableCharge | None, list[str]]:
        findings: list[str] = []
        accepted = payload.get("accepted") or {}
        requirements = payload.get("paymentRequirements") or {}
        signed = payload.get("payload") or {}
        permit = signed.get("permit2Authorization") or {}
        permitted = permit.get("permitted") or {}
        if accepted.get("scheme") != "upto" or requirements.get("scheme") != "upto":
            findings.append("scheme is not upto")
        if accepted.get("network") not in self.networks:
            findings.append("network not allowlisted")
        if accepted.get("asset") not in self.assets or accepted.get("payTo") not in self.payees:
            findings.append("asset or payee not allowlisted")
        if not signed.get("signature") or not permit:
            findings.append("Permit2 signature or authorization missing")
        try:
            ceiling = int(permitted["amount"])
            actual = int(requirements["amount"])
        except (KeyError, TypeError, ValueError):
            findings.append("ceiling and actual amount must be atomic-unit integers")
            return None, findings
        charge = VariableCharge(ceiling, actual)
        findings.extend(charge.validate())
        if str(accepted.get("amount")) != str(ceiling):
            findings.append("accepted amount does not equal signed ceiling")
        return charge, findings

    def verify_authority(self, payload: dict) -> BindingResult:
        charge, findings = self._charge(payload)
        if charge is not None and charge.actual != charge.ceiling:
            findings.append("verification-time amount must equal signed ceiling")
        if findings:
            return BindingResult(BindingDecision.REJECT, findings=findings,
                                 reason="; ".join(findings))
        return self._authoritative_verify(payload)

    def _authoritative_verify(self, payload: dict) -> BindingResult:
        request = self._request(payload)
        digest = self._request_digest(request)
        try:
            evidence = self.verifier.verify(request)
        except Exception as exc:
            return BindingResult(BindingDecision.HALT, reason=type(exc).__name__)
        ok = (evidence.is_valid and evidence.authenticated
              and evidence.request_digest == digest
              and evidence.facilitator_id in self.trusted_facilitators)
        return BindingResult(BindingDecision.ACCEPT if ok else BindingDecision.REJECT,
                             assurance=self.max_native_assurance if ok else AssuranceLevel.NONE,
                             finality=SettlementFinality.IRREVERSIBLE,
                             reason="authoritative upto verification" if ok else "untrusted upto verification")

    def verify_variable_settlement(self, payload: dict) -> BindingResult:
        _, findings = self._charge(payload)
        if findings:
            return BindingResult(BindingDecision.REJECT, findings=findings,
                                 reason="; ".join(findings))
        request = self._request(payload)
        try:
            evidence = self.verifier.settlement(request)
        except Exception as exc:
            return BindingResult(BindingDecision.HALT, reason=type(exc).__name__)
        requirements = payload.get("paymentRequirements") or {}
        ok = (evidence.success and evidence.authenticated
              and evidence.request_digest == self._request_digest(request)
              and evidence.facilitator_id in self.trusted_facilitators
              and evidence.network == (payload.get("accepted") or {}).get("network")
              and evidence.amount == str(requirements.get("amount")))
        if evidence.amount == "0" and evidence.transaction == "":
            pass
        elif not evidence.transaction:
            ok = False
        return BindingResult(BindingDecision.ACCEPT if ok else BindingDecision.REJECT,
                             assurance=self.max_native_assurance if ok else AssuranceLevel.NONE,
                             reason="bounded variable settlement" if ok else "variable settlement evidence rejected")


class X402V2EscrowBinding(X402V2UptoBinding):
    """SafePay Escrow (`X402V2EscrowBinding`): SVM upto/escrow."""

    human_name = "SafePay Escrow"
    technical_name = "X402V2EscrowBinding"
    payment_flow = "escrow"

    def __init__(self, *, verifier: X402AuthoritativeVerifier,
                 trusted_facilitators: set[str], **kwargs):
        super().__init__(verifier=verifier, trusted_facilitators=trusted_facilitators,
                         **kwargs)
        self._phases: dict[str, EscrowPhase] = {}
        self._lock = threading.RLock()

    def settle_phase(self, payload: dict) -> BindingResult:
        signed = payload.get("payload") or {}
        channel = signed.get("channelId")
        phase = signed.get("type")
        if not channel or phase not in {"deposit", "claim"}:
            return BindingResult(BindingDecision.REJECT,
                                 reason="channelId and explicit deposit/claim type required")
        with self._lock:
            current = self._phases.get(channel, EscrowPhase.NEW)
            if phase == "deposit":
                if current is not EscrowPhase.NEW:
                    return BindingResult(BindingDecision.REJECT, reason="duplicate escrow deposit")
                result = self.verifier.settlement(self._request(payload))
                if not self._trusted_settlement(payload, result):
                    return BindingResult(BindingDecision.REJECT, reason="deposit evidence rejected")
                self._phases[channel] = EscrowPhase.DEPOSITED
                return BindingResult(BindingDecision.ACCEPT, assurance=self.max_native_assurance,
                                     reason="escrow deposit committed")
            if current is not EscrowPhase.DEPOSITED:
                return BindingResult(BindingDecision.REJECT, reason="claim before deposit")
            if not signed.get("voucherSignature"):
                return BindingResult(BindingDecision.REJECT, reason="claim/refund voucher missing")
            result = self.verifier.settlement(self._request(payload))
            if not self._trusted_settlement(payload, result):
                return BindingResult(BindingDecision.REJECT, reason="claim evidence rejected")
            self._phases[channel] = EscrowPhase.CLOSED
            return BindingResult(BindingDecision.ACCEPT, assurance=self.max_native_assurance,
                                 reason="escrow claim/refund committed")

    def _trusted_settlement(self, payload: dict, evidence) -> bool:
        request = self._request(payload)
        return bool(evidence.success and evidence.authenticated
                    and evidence.request_digest == self._request_digest(request)
                    and evidence.facilitator_id in self.trusted_facilitators
                    and evidence.network == (payload.get("accepted") or {}).get("network")
                    and evidence.amount == str((payload.get("paymentRequirements") or {}).get("amount")))
