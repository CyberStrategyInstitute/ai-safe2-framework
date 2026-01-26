"""
AI SAFE² Static Analysis Engine
Copyright (c) 2025 Cyber Strategy Institute
"""
import os
import re
import math
import json
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel

# --- DATA MODELS ---

class Violation(BaseModel):
    control_id: str
    severity: str
    file_path: str
    line_number: int
    evidence: str
    remediation: str

class ScanResult(BaseModel):
    score: float
    verdict: str
    violations: List[Violation]
    controls_failed: List[str]
    meta: Dict[str, Any]

# --- LOGIC CORE ---

class StaticScanner:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        # Hardcoded High-Confidence Patterns (The "Deterministic" Layer)
        self.patterns = [
            # P1.T1.4 (NHI Hygiene)
            (r"(sk-[a-zA-Z0-9]{32,})", "P1.T1.4_ADV", "CRITICAL", "Hardcoded OpenAI Key detected."),
            (r"(ghp_[a-zA-Z0-9]{36})", "P1.T1.4_ADV", "CRITICAL", "Hardcoded GitHub Token detected."),
            (r"-----BEGIN PRIVATE KEY-----", "P1.T1.4_ADV", "CRITICAL", "RSA Private Key detected."),
            
            # P1.T2.1 (Sandboxing)
            (r"shell=True", "P1.T2.1", "HIGH", "Unsafe subprocess execution (Shell Injection Risk)."),
            (r"eval\(", "P1.T2.1", "HIGH", "Usage of 'eval()' detected. Code Injection Risk."),
            
            # P1.T2.2 (Network)
            (r"0\.0\.0\.0", "P1.T2.2", "MEDIUM", "Binding to all interfaces (Exposure Risk)."),
            
            # P3.T5.1 (Fail-Safe)
            (r"while True:", "P3.T5.1", "MEDIUM", "Infinite loop detected without obvious break (Runaway Risk)."),
        ]

    def _calculate_entropy(self, text: str) -> float:
        """Shannon Entropy calculation for secret detection"""
        if not text: return 0
        entropy = 0
        for x in range(256):
            p_x = float(text.count(chr(x))) / len(text)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def scan_project(self, root_path: str) -> ScanResult:
        violations = []
        controls_failed = set()
        
        # Walk the tree
        for root, _, files in os.walk(root_path):
            if "node_modules" in root or ".git" in root or "venv" in root:
                continue # Skip junk folders

            for file in files:
                if file.endswith((".py", ".js", ".ts", ".env", ".json", ".yaml")):
                    full_path = Path(root) / file
                    try:
                        content = full_path.read_text(encoding="utf-8", errors="ignore")
                        lines = content.split('\n')
                        
                        # 1. Regex Scan
                        for i, line in enumerate(lines):
                            # Skip comments (Basic heuristic)
                            if line.strip().startswith("#") or line.strip().startswith("//"):
                                continue

                            for pattern, control, severity, msg in self.patterns:
                                if re.search(pattern, line):
                                    violations.append(Violation(
                                        control_id=control,
                                        severity=severity,
                                        file_path=str(full_path),
                                        line_number=i + 1,
                                        evidence=line.strip()[:60], # Truncate for display
                                        remediation=f"See AI SAFE2 Control {control} in Documentation."
                                    ))
                                    controls_failed.add(control)

                        # 2. Entropy Scan (For secrets that don't match regex)
                        # Scan 50-char chunks for high entropy
                        for i, line in enumerate(lines):
                            words = line.split()
                            for word in words:
                                if len(word) > 20 and self._calculate_entropy(word) > 4.5:
                                    # Filter out common false positives (URLs, long vars)
                                    if "http" not in word and "/" not in word:
                                        violations.append(Violation(
                                            control_id="P1.T1.4_ADV",
                                            severity="HIGH",
                                            file_path=str(full_path),
                                            line_number=i + 1,
                                            evidence=f"High Entropy String: {word[:10]}...",
                                            remediation="Verify this is not a secret/key."
                                        ))
                                        controls_failed.add("P1.T1.4_ADV")

                    except Exception as e:
                        # Log error but continue scanning
                        pass

        # Calculate Score (Simple weighting)
        # 100 - (Critical * 10) - (High * 5) - (Medium * 2)
        penalty = 0
        for v in violations:
            if v.severity == "CRITICAL": penalty += 10
            elif v.severity == "HIGH": penalty += 5
            elif v.severity == "MEDIUM": penalty += 2
        
        final_score = max(0, 100 - penalty)
        
        verdict = "SECURE"
        if final_score < 50: verdict = "CRITICAL FAIL"
        elif final_score < 80: verdict = "AT RISK"

        return ScanResult(
            score=final_score,
            verdict=verdict,
            violations=violations,
            controls_failed=list(controls_failed),
            meta={"scanned_path": root_path, "framework": "v2.1"}
        )
