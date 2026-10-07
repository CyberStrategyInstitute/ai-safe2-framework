test file                                                  | RED: main 83de4a8                        | GREEN: branch 21a8333
---|---|---
NEXUS/sdk/python/tests/test_agbom_integrity.py             | 7 failed, 2 passed in 0.10s              | 9 passed in 0.05s 
NEXUS/sdk/python/tests/test_guardian_evasion.py            | 24 failed, 9 passed in 0.21s             | 33 passed in 0.08s 
NEXUS/sdk/python/tests/test_guardian_remote_failover.py    | 2 failed, 1 passed in 0.25s              | 3 passed in 0.10s 
NEXUS/sdk/python/tests/test_memory_vaccine_honesty.py      | 4 failed in 0.04s                        | 4 passed in 0.03s 
NEXUS/sdk/python/tests/test_nexus_score_honesty.py         | 2 failed in 0.25s                        | 2 passed in 0.86s 
tests/mcp_toolkit/test_scan_coverage.py                    | 7 failed in 0.20s                        | 7 passed in 0.91s
tests/mcp_toolkit/test_score_gaming.py                     | 6 failed, 1 passed in 0.41s              | 7 passed in 0.19s
tests/mcp_toolkit/test_wrap_enforcement.py                 | 1 error in 0.16s                         | 7 passed in 3.98s
tests/test_gate_false_assurance.py                         | 13 failed, 4 passed in 0.38s             | 17 passed in 0.27s
skills/mcp/tests/test_honest_outputs.py                    | no result (collection/import failure)    | 5 passed in 0.11s
skills/mcp/tests/test_transport_e2e.py                     | no result (collection/import failure)    | 6 passed, 2 warnings in 5.28s
NEXUS/opa/nexus_authz_test.rego (+ policies)               | OPA 0.65: 7 errors occurred:             | OPA 1.4.2: PASS: 16/16 
NEXUS/opa/nexus_aism_invariants_test.rego (+ policies)     | OPA 0.65: 7 errors occurred:             | OPA 1.4.2: PASS: 16/16 
