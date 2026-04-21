"""
AI SAFE² v3.0 Report Generator
Generates structured compliance evidence artifacts.

Upgraded from v2.1 (2 ISO clauses, one placeholder) to v3.0:
  - Full 32-framework compliance mapping
  - Per-pillar scoring breakdown
  - ACT tier and governance gap reporting
  - v3.0 Combined Risk Score components
  - SARIF output for IDE and CI/CD integration
"""
from __future__ import annotations

import json
import time
from datetime import datetime, UTC
from pathlib import Path

try:
    from .scanner import ScanResult, Violation
except ImportError:
    from scanner import ScanResult, Violation


# ── Framework Display Names ───────────────────────────────────────────────────

FRAMEWORK_NAMES = {
    "NIST_AI_RMF":         "NIST AI RMF 1.0/2.0",
    "ISO_42001":           "ISO/IEC 42001:2023",
    "OWASP_AIVSS_v0.8":   "OWASP AIVSS v0.8",
    "OWASP_LLM_Top10":    "OWASP Top 10 LLM",
    "OWASP_Agentic_Top10": "OWASP Agentic Top 10 (ASI)",
    "MITRE_ATLAS":         "MITRE ATLAS (Oct 2025)",
    "MIT_AI_Risk_v4":      "MIT AI Risk Repository v4",
    "Google_SAIF":         "Google SAIF",
    "CSA_Agentic_CP":      "CSA Agentic Control Plane",
    "CSA_Zero_Trust_LLMs": "CSA Zero Trust for LLMs",
    "MAESTRO":             "MAESTRO (CSA 7-Layer)",
    "Arcanum_PI":          "Arcanum PI Taxonomy",
    "AIDEFEND":            "AIDEFEND (7 Tactics)",
    "AIID":                "AIID Agentic Incidents",
    "EU_AI_Act":           "EU AI Act (2024)",
    "Intl_AI_Safety_2026": "International AI Safety Report 2026",
    "CSETv1":              "CSETv1 Harm",
    "HIPAA":               "HIPAA",
    "PCI_DSS_v4":          "PCI-DSS v4.0",
    "SOC2_Type2":          "SOC 2 Type II",
    "ISO_27001":           "ISO 27001:2022",
    "NIST_CSF_2":          "NIST CSF 2.0",
    "NIST_SP800_53":       "NIST SP 800-53 Rev 5",
    "FedRAMP":             "FedRAMP",
    "CMMC_2":              "CMMC 2.0",
    "CIS_v8":              "CIS Controls v8",
    "GDPR":                "GDPR",
    "CCPA_CPRA":           "CCPA / CPRA",
    "SEC_Disclosure":      "SEC Cyber Disclosure",
    "DORA":                "DORA",
    "CVE_CVSS":            "CVE / CVSS",
    "Zero_Trust":          "Zero Trust",
}

# Key compliance mappings for common frameworks even without the full JSON loaded
FALLBACK_FRAMEWORK_MAPPINGS: dict[str, list[str]] = {
    "NIST_AI_RMF":     ["P1", "P2", "P3", "P4", "P5", "CP.3", "CP.4"],
    "ISO_42001":       ["P1.T1", "P2.T3", "P4.T7", "P5.T9", "CP.6"],
    "SOC2_Type2":      ["P1.T2.9", "P4.T8.3", "A2.5", "CP.10"],
    "GDPR":            ["P1.T1.5", "P2.T3.7", "CP.10"],
    "EU_AI_Act":       ["P4.T7.1", "CP.3", "CP.8", "CP.10"],
    "HIPAA":           ["P1.T1.5", "P3.T6", "P2.T3.1"],
    "PCI_DSS_v4":      ["P1.T1.5", "P1.T2.2", "P2.T3.1", "M4.8"],
    "OWASP_LLM_Top10": ["P1.T1.2", "P1.T1.10", "S1.6"],
    "OWASP_Agentic_Top10": ["CP.9", "CP.10", "S1.5", "F3.2"],
    "MITRE_ATLAS":     ["P1.T1.2", "P1.T1.10", "S1.4", "E5.4"],
    "Zero_Trust":      ["P1.T2.2", "P1.T2.9", "CP.4"],
    "DORA":            ["P3.T5.10", "P3.T6", "CP.6", "E5.1"],
}


class ISO42001Report:
    """Main report class — backward compatible with v2.1 interface."""

    def generate_report(
        self,
        result: ScanResult,
        output_path: str = "ai_safe2_audit_report.json",
        include_sarif: bool = False,
    ) -> str:
        """
        Generate a v3.0 compliance evidence artifact.

        Args:
            result:       ScanResult from StaticScanner.scan_project()
            output_path:  Where to write the JSON report
            include_sarif: Also write a SARIF file for IDE/CI integration

        Returns:
            Path to the generated report file
        """
        artifact = self._build_artifact(result)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)

        print(f"\n📄 AI SAFE2 v3.0 Compliance Report: {output_path}")
        print(f"   Score:   {result.score}/100 — {result.verdict}")
        print(f"   Findings: {len(result.violations)} violations across {len(result.controls_failed)} controls")

        if result.act_estimate:
            act = result.act_estimate
            print(f"   ACT Tier: {act.get('estimated_tier', 'unknown')} "
                  f"({act.get('confidence', '?')} confidence)")
            if act.get("hear_required"):
                print("   ⚠️  HEAR Required: Designate a Human Ethical Agent of Record before deployment")
            if act.get("cp9_required"):
                print("   ⚠️  CP.9 Required: Agent Replication Governance must be implemented")

        if result.governance_gaps:
            print(f"\n   Governance Gaps ({len(result.governance_gaps)}):")
            for gap in result.governance_gaps[:3]:
                print(f"     • {gap[:90]}...")

        if include_sarif:
            sarif_path = output_path.replace(".json", ".sarif.json")
            sarif = self._build_sarif(result)
            with open(sarif_path, "w", encoding="utf-8") as f:
                json.dump(sarif, f, indent=2)
            print(f"   SARIF:   {sarif_path}")

        return output_path

    def _build_artifact(self, result: ScanResult) -> dict:
        """Build the full JSON compliance artifact."""

        # ── Framework compliance mapping ───────────────────────────────────
        framework_status: dict[str, dict] = {}

        # Build set of failed control IDs
        failed_controls = set(result.controls_failed)

        for fw_id, fw_name in FRAMEWORK_NAMES.items():
            # Collect evidence from violations mapped to this framework
            evidence = []
            for v in result.violations:
                if fw_id in (v.compliance_frameworks or []):
                    evidence.append(v.dict() if hasattr(v, "dict") else {
                        "control_id": v.control_id,
                        "severity": v.severity,
                        "file_path": v.file_path,
                        "line_number": v.line_number,
                        "evidence": v.evidence,
                    })

            # Also check fallback mappings
            fallback_controls = FALLBACK_FRAMEWORK_MAPPINGS.get(fw_id, [])
            fallback_hits = [c for c in fallback_controls if any(
                fc.startswith(c) for fc in failed_controls
            )]
            if not evidence and fallback_hits:
                evidence = [{"control_id": c, "note": "Fallback mapping"} for c in fallback_hits]

            status = "FAIL" if evidence else "PASS"
            framework_status[fw_id] = {
                "framework_name": fw_name,
                "status": status,
                "violation_count": len(evidence),
                "evidence": evidence[:10],  # cap at 10 per framework to keep report size reasonable
            }

        # ── Pillar breakdown ───────────────────────────────────────────────
        pillar_breakdown: dict[str, dict] = {}
        for pid in ("P1", "P2", "P3", "P4", "P5", "CP"):
            pillar_vs = [v for v in result.violations if v.control_id.startswith(pid)]
            crit = sum(1 for v in pillar_vs if v.severity == "CRITICAL")
            high = sum(1 for v in pillar_vs if v.severity == "HIGH")
            pillar_breakdown[pid] = {
                "score": result.meta.get("pillar_scores", {}).get(pid, 100),
                "violation_count": len(pillar_vs),
                "critical": crit,
                "high": high,
                "controls_failed": sorted(set(v.control_id for v in pillar_vs)),
            }

        # ── Sort findings by severity ──────────────────────────────────────
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        sorted_violations = sorted(
            result.violations,
            key=lambda v: sev_order.get(v.severity, 5)
        )

        artifact = {
            "report_type": "AI SAFE2 v3.0 Compliance Evidence",
            "framework_version": "3.0.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "generated_at_ts": time.time(),
            "target": result.meta.get("scanned_path", "unknown"),
            "controls_json_loaded": result.meta.get("controls_json_loaded", False),

            # ── Summary ────────────────────────────────────────────────────
            "summary": {
                "score": result.score,
                "verdict": result.verdict,
                "total_violations": len(result.violations),
                "controls_failed": result.controls_failed,
                "by_severity": {
                    "CRITICAL": sum(1 for v in result.violations if v.severity == "CRITICAL"),
                    "HIGH":     sum(1 for v in result.violations if v.severity == "HIGH"),
                    "MEDIUM":   sum(1 for v in result.violations if v.severity == "MEDIUM"),
                    "LOW":      sum(1 for v in result.violations if v.severity == "LOW"),
                },
            },

            # ── Risk Score ─────────────────────────────────────────────────
            "risk_score": result.risk_formula_components,

            # ── ACT Tier Assessment ────────────────────────────────────────
            "act_tier_assessment": result.act_estimate,

            # ── Governance Gaps ────────────────────────────────────────────
            "governance_gaps": result.governance_gaps,

            # ── Pillar Breakdown ───────────────────────────────────────────
            "pillar_breakdown": pillar_breakdown,

            # ── All Findings (sorted by severity) ─────────────────────────
            "findings": [
                {
                    "id": f"F{i+1:04d}",
                    "control_id": v.control_id,
                    "control_name": v.control_name,
                    "severity": v.severity,
                    "pillar": v.pillar,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "evidence": v.evidence,
                    "description": v.description,
                    "remediation": v.remediation,
                    "compliance_frameworks": v.compliance_frameworks,
                }
                for i, v in enumerate(sorted_violations)
            ],

            # ── 32-Framework Compliance Map ────────────────────────────────
            "framework_compliance": framework_status,

            # ── Compliance Summary Counts ──────────────────────────────────
            "compliance_summary": {
                "frameworks_passing": sum(1 for f in framework_status.values() if f["status"] == "PASS"),
                "frameworks_failing": sum(1 for f in framework_status.values() if f["status"] == "FAIL"),
                "total_frameworks": len(framework_status),
            },

            # ── Metadata ───────────────────────────────────────────────────
            "meta": {
                **result.meta,
                "scanner_version": "3.0.0",
                "toolkit_url": "https://cyberstrategyinstitute.com/ai-safe2/",
                "framework_url": "https://github.com/CyberStrategyInstitute/ai-safe2-framework",
            },
        }

        return artifact

    def _build_sarif(self, result: ScanResult) -> dict:
        """
        Build a SARIF 2.1.0 output for IDE and CI/CD integration.
        Compatible with GitHub Code Scanning, VS Code SARIF Viewer, etc.
        """
        rules_sarif = {}
        for v in result.violations:
            if v.control_id not in rules_sarif:
                rules_sarif[v.control_id] = {
                    "id": v.control_id,
                    "name": v.control_name or v.control_id,
                    "shortDescription": {"text": v.description or v.control_id},
                    "fullDescription": {"text": v.remediation},
                    "helpUri": "https://github.com/CyberStrategyInstitute/ai-safe2-framework",
                    "properties": {
                        "tags": ["security", "ai-safety", "ai-safe2"],
                        "compliance": v.compliance_frameworks,
                    },
                }

        sev_map = {"CRITICAL": "error", "HIGH": "error", "MEDIUM": "warning",
                   "LOW": "note", "INFO": "none"}

        results_sarif = [
            {
                "ruleId": v.control_id,
                "level": sev_map.get(v.severity, "warning"),
                "message": {"text": f"[{v.control_id}] {v.description} | Fix: {v.remediation[:120]}"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": v.file_path},
                        "region": {"startLine": max(1, v.line_number)},
                    }
                }],
            }
            for v in result.violations
        ]

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "AI SAFE2 Scanner",
                        "version": "3.0.0",
                        "informationUri": "https://github.com/CyberStrategyInstitute/ai-safe2-framework",
                        "rules": list(rules_sarif.values()),
                    }
                },
                "results": results_sarif,
            }],
        }


# Backward compatible instance
iso42001 = ISO42001Report()
