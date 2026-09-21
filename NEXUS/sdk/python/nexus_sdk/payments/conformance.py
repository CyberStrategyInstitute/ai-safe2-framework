"""RailGuard Contract and RailGuard Lab for payment-protocol bindings."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from nexus_sdk.payments.adapters import BindingDecision, BindingResult, RailBinding
from nexus_sdk.payments.objects import AssuranceLevel, SettlementFinality

__all__ = [
    "RailBindingContract",
    "RailBindingCase",
    "ConformanceFinding",
    "ConformanceReport",
    "RailBindingConformanceSuite",
]


@dataclass(frozen=True)
class RailBindingContract:
    """RailGuard Contract (`RailBindingContract`).

    The explicit support tuple prevents a broad protocol name from silently
    implying support for every version, asset, network, flow, or finality model.
    """

    human_name: str
    technical_name: str
    protocol: str
    protocol_version: str
    scheme: str
    networks: frozenset[str]
    assets: frozenset[str]
    payment_flow: str
    finality: SettlementFinality
    max_native_assurance: AssuranceLevel
    authoritative_verification: bool = False

    def validate(self) -> list[str]:
        findings: list[str] = []
        for name in (
            "human_name", "technical_name", "protocol", "protocol_version",
            "scheme", "payment_flow",
        ):
            if not getattr(self, name).strip():
                findings.append(f"contract.{name} is required")
        if not self.networks:
            findings.append("contract.networks must be explicit and non-empty")
        if not self.assets:
            findings.append("contract.assets must be explicit and non-empty")
        if self.max_native_assurance >= AssuranceLevel.RUNTIME_BOUND:
            findings.append("a rail binding cannot claim native Runtime Proof")
        if (not self.authoritative_verification
                and self.max_native_assurance > AssuranceLevel.NONE):
            findings.append(
                "non-authoritative verification must declare native assurance NONE"
            )
        return findings


@dataclass(frozen=True)
class RailBindingCase:
    """One public, synthetic vector. Payload contents are never copied to reports."""

    name: str
    payload: dict[str, Any]
    canonical_digest: str
    expected_authority: BindingDecision
    expected_binding: BindingDecision
    expected_finality: Optional[SettlementFinality] = None


@dataclass(frozen=True)
class ConformanceFinding:
    case: str
    control: str
    detail: str


@dataclass
class ConformanceReport:
    contract_name: str
    findings: list[ConformanceFinding] = field(default_factory=list)
    cases_run: int = 0

    @property
    def passed(self) -> bool:
        return not self.findings

    def add(self, case: str, control: str, detail: str) -> None:
        self.findings.append(ConformanceFinding(case, control, detail))

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_name": self.contract_name,
            "passed": self.passed,
            "cases_run": self.cases_run,
            "findings": [
                {"case": item.case, "control": item.control, "detail": item.detail}
                for item in self.findings
            ],
            "privacy": "payloads omitted",
        }


class RailBindingConformanceSuite:
    """RailGuard Lab (`RailBindingConformanceSuite`)."""

    human_name = "RailGuard Lab"
    technical_name = "RailBindingConformanceSuite"

    def evaluate(
        self,
        binding: RailBinding,
        contract: RailBindingContract,
        cases: Iterable[RailBindingCase],
    ) -> ConformanceReport:
        report = ConformanceReport(contract.human_name)
        for detail in contract.validate():
            report.add("contract", "declaration", detail)
        if binding.protocol != contract.protocol:
            report.add("contract", "protocol", "binding protocol differs from contract")
        if binding.max_native_assurance != contract.max_native_assurance:
            report.add("contract", "assurance", "binding assurance differs from contract")

        for case in cases:
            report.cases_run += 1
            self._evaluate_case(binding, contract, case, report)
        if report.cases_run == 0:
            report.add("contract", "coverage", "at least one conformance case is required")
        return report

    def _evaluate_case(
        self,
        binding: RailBinding,
        contract: RailBindingContract,
        case: RailBindingCase,
        report: ConformanceReport,
    ) -> None:
        original = deepcopy(case.payload)
        authority = self._invoke(
            report, case.name, "authority", binding.verify_authority, case.payload
        )
        transaction = self._invoke(
            report, case.name, "canonical-binding", binding.bind_transaction,
            case.payload, case.canonical_digest,
        )
        if case.payload != original:
            report.add(case.name, "input-integrity", "binding mutated caller payload")
        self._expect(report, case.name, "authority", authority, case.expected_authority)
        self._expect(report, case.name, "canonical-binding", transaction,
                     case.expected_binding)

        for label, result in (("authority", authority), ("canonical-binding", transaction)):
            if result is None:
                continue
            if result.assurance > contract.max_native_assurance:
                report.add(case.name, "assurance", f"{label} exceeded declared ceiling")
            if (result.decision is BindingDecision.ACCEPT
                    and label == "canonical-binding"
                    and result.canonical_digest != case.canonical_digest):
                report.add(case.name, "canonical-binding",
                           "accepted result did not return the requested digest")

        assurance = self._invoke(
            report, case.name, "assurance", binding.assurance_of, case.payload
        )
        if isinstance(assurance, AssuranceLevel):
            if assurance > contract.max_native_assurance:
                report.add(case.name, "assurance", "reported assurance exceeded ceiling")
            if (authority is not None
                    and authority.decision is not BindingDecision.ACCEPT
                    and assurance is not AssuranceLevel.NONE):
                report.add(case.name, "assurance", "rejected authority retained assurance")

        if case.expected_finality is not None:
            finality = self._invoke(
                report, case.name, "finality", binding.finality_of, case.payload
            )
            if finality is not None and finality != case.expected_finality:
                report.add(case.name, "finality", "reported finality differs from vector")

        # Reconciliation without an idempotency key or resolver must halt. It
        # must never manufacture acceptance from an incomplete payload.
        if not case.payload.get("idempotencyKey"):
            reconciliation = self._invoke(
                report, case.name, "reconciliation", binding.reconcile, case.payload
            )
            if (reconciliation is not None
                    and reconciliation.decision is not BindingDecision.HALT):
                report.add(case.name, "reconciliation",
                           "missing idempotency key did not halt")

    @staticmethod
    def _invoke(report: ConformanceReport, case: str, control: str, function, *args):
        try:
            return function(*args)
        except Exception as exc:
            report.add(case, control, f"raised {type(exc).__name__}")
            return None

    @staticmethod
    def _expect(report: ConformanceReport, case: str, control: str,
                result: Optional[BindingResult], expected: BindingDecision) -> None:
        if result is None:
            return
        if not isinstance(result, BindingResult):
            report.add(case, control, "did not return BindingResult")
        elif result.decision is not expected:
            report.add(case, control,
                       f"expected {expected.value}, received {result.decision.value}")
