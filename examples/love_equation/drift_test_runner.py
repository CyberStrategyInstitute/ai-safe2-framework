#!/usr/bin/env python3
"""
Love Equation Drift Test Runner
================================

Executes drift test suites defined in YAML and validates alignment evaluator
behavior against expected outcomes.

Supports both probabilistic tests (with statistical validation) and
deterministic tests (with exact reproducibility requirements).

Usage:
    python drift_test_runner.py --suite probabilistic
    python drift_test_runner.py --suite deterministic
    python drift_test_runner.py --all

Author: Cyber Strategy Institute
License: MIT
"""

import argparse
import json
import yaml
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import numpy as np
from dataclasses import dataclass, asdict

# Import the evaluator
from evaluator import LoveEquationEvaluator, AlignmentBand


@dataclass
class TestResult:
    """Result of a single test run"""
    test_name: str
    suite_type: str  # "probabilistic" or "deterministic"
    passed: bool
    iterations_run: int
    expected_outcome: Dict
    actual_outcome: Dict
    drift_percentage: float
    errors: List[str]
    warnings: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DriftTestRunner:
    """Executes drift tests from YAML specifications"""
    
    def __init__(self, test_dir: Path = Path("drift_tests")):
        self.test_dir = test_dir
        self.results: List[TestResult] = []
        
    def load_test_suite(self, suite_name: str) -> Dict:
        """Load a YAML test suite"""
        suite_path = self.test_dir / f"{suite_name}.yaml"
        
        if not suite_path.exists():
            raise FileNotFoundError(f"Test suite not found: {suite_path}")
        
        with open(suite_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_event_from_distribution(self, 
                                        event_dist: Dict, 
                                        mag_dist: Dict,
                                        ctx_dist: Dict,
                                        agent_id: str) -> Dict:
        """Generate a single event based on distribution parameters"""
        
        # Determine cooperation vs defection
        coop_rate = event_dist.get("cooperation_rate", 0.5)
        is_cooperation = np.random.random() < coop_rate
        
        # Select category
        if is_cooperation:
            categories = event_dist.get("cooperation_categories", {})
            event_type = "COOPERATION"
        else:
            categories = event_dist.get("defection_categories", {})
            event_type = "DEFECTION"
        
        # Weighted random selection of category
        cats = list(categories.keys())
        weights = list(categories.values())
        category = np.random.choice(cats, p=weights)
        
        # Generate magnitude
        if mag_dist.get("type") == "normal":
            magnitude = np.clip(
                np.random.normal(mag_dist["mean"], mag_dist["std_dev"]),
                mag_dist["min"],
                mag_dist["max"]
            )
        elif mag_dist.get("type") == "uniform":
            magnitude = np.random.uniform(mag_dist["min"], mag_dist["max"])
        else:
            magnitude = 5.0
        
        # Generate context
        stakes_dist = ctx_dist.get("stakes", {})
        stakes = np.random.choice(
            list(stakes_dist.keys()),
            p=list(stakes_dist.values())
        )
        
        rev_dist = ctx_dist.get("reversibility", {})
        reversibility = np.random.choice(
            list(rev_dist.keys()),
            p=list(rev_dist.values())
        )
        
        context = {
            "domain": "general",
            "stakes": stakes,
            "reversibility": reversibility,
            "sensitive_data": np.random.random() < ctx_dist.get("sensitive_data_rate", 0.0),
            "user_vulnerable": np.random.random() < ctx_dist.get("user_vulnerable_rate", 0.0),
            "financial_impact": np.random.random() < ctx_dist.get("financial_impact_rate", 0.0),
            "self_harm_risk": np.random.random() < ctx_dist.get("self_harm_risk_rate", 0.0),
            "third_party_impact": np.random.random() < ctx_dist.get("third_party_impact_rate", 0.0)
        }
        
        # Generate verifiability and confidence
        verif_dist = event_dist.get("verifiability_distribution", {})
        if verif_dist.get("type") == "beta":
            verifiability = np.random.beta(verif_dist["alpha"], verif_dist["beta"])
        else:
            verifiability = 0.7
        
        conf_dist = event_dist.get("confidence_distribution", {})
        if conf_dist.get("type") == "beta":
            confidence = np.random.beta(conf_dist["alpha"], conf_dist["beta"])
        else:
            confidence = 0.7
        
        # Construct event
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": agent_id,
            "event_type": event_type,
            "category": category,
            "magnitude": float(magnitude),
            "context": context,
            "verifiability": float(verifiability),
            "confidence": float(confidence)
        }
        
        return event
    
    def run_probabilistic_test(self, test_spec: Dict, defaults: Dict) -> TestResult:
        """Run a single probabilistic test with statistical validation"""
        
        test_name = test_spec["name"]
        iterations = defaults.get("test_iterations", 10)
        event_count = defaults.get("event_count", 1000)
        
        print(f"\nRunning probabilistic test: {test_name}")
        print(f"  Description: {test_spec['description']}")
        print(f"  Iterations: {iterations}")
        print(f"  Events per iteration: {event_count}")
        
        results = []
        errors = []
        warnings = []
        
        for i in range(iterations):
            # Initialize evaluator
            initial_state = test_spec.get("initial_state", {})
            evaluator = LoveEquationEvaluator(
                beta=defaults.get("beta", 0.1),
                beta_I=defaults.get("beta_I", 0.08),
                E_initial=initial_state.get("E_initial", defaults.get("E_initial", 5.0)),
                I_initial=initial_state.get("I_initial", defaults.get("I_initial", 5.0))
            )
            
            # Generate and process events
            event_dist = test_spec["event_distribution"]
            mag_dist = test_spec["magnitude_distribution"]
            ctx_dist = test_spec["context_distribution"]
            
            for _ in range(event_count):
                event = self.generate_event_from_distribution(
                    event_dist, mag_dist, ctx_dist, f"test-{test_name}"
                )
                evaluator.process_event(event)
            
            # Collect results
            scores = evaluator.get_scores()
            results.append({
                "E_final": scores.E,
                "I_final": scores.I,
                "C_cumulative": scores.C_cumulative,
                "D_cumulative": scores.D_cumulative,
                "band": scores.band.value
            })
        
        # Statistical analysis
        E_finals = [r["E_final"] for r in results]
        I_finals = [r["I_final"] for r in results]
        
        E_mean = np.mean(E_finals)
        E_std = np.std(E_finals)
        I_mean = np.mean(I_finals)
        I_std = np.std(I_finals)
        
        # Check expected outcomes
        expected = test_spec["expected_outcome"]
        passed = True
        
        # Check E bounds
        if "E_final_min" in expected and "E_final_max" in expected:
            if E_mean < expected["E_final_min"] or E_mean > expected["E_final_max"]:
                errors.append(
                    f"E_mean ({E_mean:.2f}) outside expected range "
                    f"[{expected['E_final_min']}, {expected['E_final_max']}]"
                )
                passed = False
        
        # Check I bounds
        if "I_final_min" in expected and "I_final_max" in expected:
            if I_mean < expected["I_final_min"] or I_mean > expected["I_final_max"]:
                errors.append(
                    f"I_mean ({I_mean:.2f}) outside expected range "
                    f"[{expected['I_final_min']}, {expected['I_final_max']}]"
                )
                passed = False
        
        # Check drift tolerance
        drift_tolerance = defaults.get("drift_tolerance", 0.03)
        E_drift = E_std / E_mean if E_mean != 0 else 0
        I_drift = I_std / I_mean if I_mean != 0 else 0
        max_drift = max(E_drift, I_drift)
        
        if max_drift > drift_tolerance:
            warnings.append(
                f"Drift ({max_drift:.4f}) exceeds tolerance ({drift_tolerance})"
            )
        
        actual_outcome = {
            "E_mean": E_mean,
            "E_std": E_std,
            "I_mean": I_mean,
            "I_std": I_std,
            "E_drift": E_drift,
            "I_drift": I_drift,
            "all_bands": [r["band"] for r in results]
        }
        
        print(f"  E: {E_mean:.2f} ± {E_std:.2f} (drift: {E_drift:.4f})")
        print(f"  I: {I_mean:.2f} ± {I_std:.2f} (drift: {I_drift:.4f})")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        return TestResult(
            test_name=test_name,
            suite_type="probabilistic",
            passed=passed,
            iterations_run=iterations,
            expected_outcome=expected,
            actual_outcome=actual_outcome,
            drift_percentage=max_drift,
            errors=errors,
            warnings=warnings,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    def run_deterministic_test(self, test_spec: Dict, defaults: Dict) -> TestResult:
        """Run a single deterministic test with exact reproducibility"""
        
        test_name = test_spec["name"]
        iterations = defaults.get("test_iterations", 100)
        
        print(f"\nRunning deterministic test: {test_name}")
        print(f"  Description: {test_spec['description']}")
        print(f"  Iterations: {iterations} (should be identical)")
        
        results = []
        errors = []
        warnings = []
        
        for i in range(iterations):
            # Initialize evaluator
            initial_state = test_spec.get("initial_state", {})
            evaluator = LoveEquationEvaluator(
                beta=defaults.get("beta", 0.1),
                beta_I=defaults.get("beta_I", 0.08),
                E_initial=initial_state.get("E_initial", defaults.get("E_initial", 5.0)),
                I_initial=initial_state.get("I_initial", defaults.get("I_initial", 5.0))
            )
            
            # Process fixed event sequence
            for event in test_spec["events"]:
                # Fill in required fields
                event_copy = event.copy()
                event_copy["event_id"] = str(uuid.uuid4())
                event_copy["timestamp"] = datetime.utcnow().isoformat() + "Z"
                event_copy["agent_id"] = f"test-{test_name}"
                
                evaluator.process_event(event_copy)
            
            # Collect results
            scores = evaluator.get_scores()
            results.append({
                "E_final": scores.E,
                "I_final": scores.I,
                "C_cumulative": scores.C_cumulative,
                "D_cumulative": scores.D_cumulative,
                "band": scores.band.value
            })
        
        # Check exact reproducibility
        first_result = results[0]
        passed = True
        
        for i, result in enumerate(results[1:], 1):
            if result["E_final"] != first_result["E_final"]:
                errors.append(
                    f"E_final mismatch at iteration {i}: "
                    f"{result['E_final']} vs {first_result['E_final']}"
                )
                passed = False
            if result["I_final"] != first_result["I_final"]:
                errors.append(
                    f"I_final mismatch at iteration {i}: "
                    f"{result['I_final']} vs {first_result['I_final']}"
                )
                passed = False
        
        # Check expected exact values
        expected = test_spec["expected_outcome"]
        tolerance = expected.get("tolerance", 0.0000001)
        
        if "E_final_exact" in expected:
            E_diff = abs(first_result["E_final"] - expected["E_final_exact"])
            if E_diff > tolerance:
                errors.append(
                    f"E_final ({first_result['E_final']}) differs from expected "
                    f"({expected['E_final_exact']}) by {E_diff}"
                )
                passed = False
        
        if "I_final_exact" in expected:
            I_diff = abs(first_result["I_final"] - expected["I_final_exact"])
            if I_diff > tolerance:
                errors.append(
                    f"I_final ({first_result['I_final']}) differs from expected "
                    f"({expected['I_final_exact']}) by {I_diff}"
                )
                passed = False
        
        # Calculate drift (should be 0 for deterministic)
        E_vals = [r["E_final"] for r in results]
        drift = max(E_vals) - min(E_vals) if len(E_vals) > 1 else 0.0
        
        print(f"  E: {first_result['E_final']:.6f} (expected: {expected.get('E_final_exact', 'N/A')})")
        print(f"  I: {first_result['I_final']:.6f} (expected: {expected.get('I_final_exact', 'N/A')})")
        print(f"  Drift: {drift:.10f}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        
        return TestResult(
            test_name=test_name,
            suite_type="deterministic",
            passed=passed,
            iterations_run=iterations,
            expected_outcome=expected,
            actual_outcome=first_result,
            drift_percentage=drift,
            errors=errors,
            warnings=warnings,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    def run_suite(self, suite_name: str) -> List[TestResult]:
        """Run an entire test suite"""
        
        print(f"\n{'=' * 60}")
        print(f"Running Test Suite: {suite_name}")
        print(f"{'=' * 60}")
        
        suite = self.load_test_suite(suite_name)
        defaults = suite.get("defaults", {})
        
        results = []
        
        for test_spec in suite["test_suites"]:
            if suite_name == "probabilistic":
                result = self.run_probabilistic_test(test_spec, defaults)
            else:  # deterministic
                result = self.run_deterministic_test(test_spec, defaults)
            
            results.append(result)
            self.results.append(result)
        
        return results
    
    def generate_report(self) -> Dict:
        """Generate summary report of all test results"""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "tests": [r.to_dict() for r in self.results],
            "failures": [r.to_dict() for r in self.results if not r.passed]
        }
        
        return report
    
    def print_summary(self):
        """Print summary to console"""
        
        report = self.generate_report()
        
        print(f"\n{'=' * 60}")
        print("TEST SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Pass rate: {report['summary']['pass_rate']:.1%}")
        
        if report['failures']:
            print(f"\n{'=' * 60}")
            print("FAILURES")
            print(f"{'=' * 60}")
            for failure in report['failures']:
                print(f"\nTest: {failure['test_name']} ({failure['suite_type']})")
                for error in failure['errors']:
                    print(f"  ✗ {error}")
                for warning in failure['warnings']:
                    print(f"  ⚠ {warning}")


def main():
    parser = argparse.ArgumentParser(
        description="Run Love Equation drift tests"
    )
    parser.add_argument(
        "--suite",
        choices=["probabilistic", "deterministic"],
        help="Specific test suite to run"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all test suites"
    )
    parser.add_argument(
        "--output",
        help="Output file for JSON report"
    )
    
    args = parser.parse_args()
    
    if not args.suite and not args.all:
        parser.print_help()
        sys.exit(1)
    
    runner = DriftTestRunner()
    
    if args.all:
        runner.run_suite("probabilistic")
        runner.run_suite("deterministic")
    else:
        runner.run_suite(args.suite)
    
    runner.print_summary()
    
    if args.output:
        report = runner.generate_report()
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport written to: {args.output}")
    
    # Exit with error code if any tests failed
    sys.exit(0 if all(r.passed for r in runner.results) else 1)


if __name__ == "__main__":
    main()