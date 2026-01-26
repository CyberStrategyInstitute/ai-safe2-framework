import json
import time
from .scanner import ScanResult

class ISO42001Report:
    def generate_report(self, result: ScanResult):
        """Generates a JSON artifact compliant with GRC tools"""
        
        artifact = {
            "report_type": "AI SAFE2 Compliance Evidence",
            "framework_version": "2.1.0",
            "generated_at": time.time(),
            "target": result.meta['scanned_path'],
            "summary": {
                "score": result.score,
                "status": result.verdict,
                "total_violations": len(result.violations)
            },
            "iso_42001_mapping": {
                "A.8.4 (AI System Impact)": {
                    "status": "FAIL" if "P1.T1.4_ADV" in result.controls_failed else "PASS",
                    "evidence": [v.dict() for v in result.violations if v.control_id == "P1.T1.4_ADV"]
                },
                "B.9 (Data Management)": {
                    "status": "FAIL" if "P1.T1.5" in result.controls_failed else "PASS",
                    "evidence": [] # Placeholder for PII scan results
                }
            }
        }
        
        filename = "ai_safe2_audit_report.json"
        with open(filename, "w") as f:
            json.dump(artifact, f, indent=2)
            
        print(f"📄 Evidence Artifact Generated: {filename}")

iso42001 = ISO42001Report()
