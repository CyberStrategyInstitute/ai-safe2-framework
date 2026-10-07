# Local CI mirror (gates.sh) at 98598ed

Revision 98598ed..21a8333 differs only by: skills/codex/ai-safe2-secure-build-copilot/SKILL-CARD.md 

```
PASS     pytest tests/ scanner/tests/
PASS     check_agent_manifest
PASS     example verify aism-decision-card
PASS     example smoke aism-decision-card
PASS     example verify aism-remediation
PASS     example smoke aism-remediation
PASS     example verify environment-decision-card
PASS     example smoke environment-decision-card
PASS     build sdist+wheel
PASS     NEXUS SDK tests
PASS     nexus-score --v03-checks (OPA)
PASS     opa check --strict (1.x)
PASS     opa test (1.x)
PASS     opa fmt (1.x)
PASS     opa check --strict (0.65)
PASS     opa test (0.65)
PASS     NEXUS example sovereign_gateway
PASS     NEXUS example acs_bridge
PASS     skills/mcp tests
PASS     ruff E9,F63,F7,F82
PASS     check_repo_ux
PASS     examples table --check
PASS     v31 MCP profile tests
PASS     v31 persistence compat
PASS     MCP profile / dashboard parity
PASS     semgrep .semgrep/security.yml
PASS     gitleaks (HEAD history, baseline)
PASS     release: clean wheel install
PASS     release: check_release_installation
PASS     release: challenge offline workflow
gates failed: 0  (logs: /tmp/claude-0/gates-98598ed)
```

## Log tails

### MCP_profile___dashboard_parity
```
```

### NEXUS_SDK_tests
```

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 608 passed, 22 warnings in 4.75s =======================
```

### NEXUS_example_acs_bridge
```
  3. Memory writes carry cryptographic provenance through ACS wire format
  4. Bridge produces standard AOS JSON-RPC 2.0 -- no ACS code changes needed
  5. Deny parsing from ACS verdict produces GuardianVerdictResult correctly
```

### NEXUS_example_sovereign_gateway
```
In production: NOR spans flow via OTel Collector to SIEM.
               OPA runs as isolated sidecar; agents cannot read policies.
               Reference deployment: docker/docker-compose.yml
```

### build_sdist_wheel
```
  - hatchling==1.32.4
* Building wheel...
Successfully built ai_safe2-1.0.0.tar.gz and ai_safe2-1.0.0-py3-none-any.whl
```

### check_agent_manifest
```
Agent manifest check passed
```

### check_repo_ux
```
Repository UX check passed
```

### example_smoke_aism_decision_card
```
AISM Decision Card example: PASS
```

### example_smoke_aism_remediation
```
{"gate": "ready_for_human_decision", "remediation_authorized": false, "conformance_claim": false}
```

### example_smoke_environment_decision_card
```
  "manifest_invalid": 0,
  "output": "<path>
}
```

### example_verify_aism_decision_card
```
    "completeness": 1.0
  }
}
```

### example_verify_aism_remediation
```
    "conformance_claim": false
  }
}
```

### example_verify_environment_decision_card
```
    "output": "<path>
  }
}
```

### examples_table___check
```
examples/README.md index already up to date
```

### gitleaks__HEAD_history__baseline_
```
[90m12:51PM[0m [32mINF[0m [1m503 commits scanned.[0m
[90m12:51PM[0m [32mINF[0m [1mscanned ~13170778 bytes (13.17 MB) in 2.43s[0m
[90m12:51PM[0m [32mINF[0m [1mno leaks found[0m
```

### nexus_score___v03_checks__OPA_
```

10 verified, 0 failed, 0 not assessed (of 10)

```

### opa_check___strict__0_65_
```
```

### opa_check___strict__1_x_
```
```

### opa_fmt__1_x_
```
```

### opa_test__0_65_
```
PASS: 16/16
```

### opa_test__1_x_
```
PASS: 16/16
```

### pytest_tests__scanner_tests_
```
........................................................................ [ 96%]
.....................................                                    [100%]
965 passed, 8 skipped in 92.35s (0:01:32)
```

### release__challenge_offline_workflow
```
    "Packaged fixture identity only; no live deployment was assessed."
  ]
}
```

### release__check_release_installation
```
```

### release__clean_wheel_install
```
```

### ruff_E9_F63_F7_F82
```
All checks passed!
```

### semgrep__semgrep_security_yml
```
```

### skills_mcp_tests
```
SKIPPED [1] tests/test_smoke_https.py:145: MCP_SERVER_URL not set — skipping HTTPS smoke tests
SKIPPED [1] tests/test_smoke_https.py:150: MCP_SERVER_URL not set — skipping HTTPS smoke tests
148 passed, 11 skipped, 2 warnings in 5.63s
```

### v31_MCP_profile_tests
```
.....                                                                    [100%]
5 passed in 0.03s
```

### v31_persistence_compat
```

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 7 passed, 4 warnings in 0.03s =========================
```
