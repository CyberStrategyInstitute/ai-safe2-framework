# Battery delta: main 83de4a8 vs branch, same harness

Cases red/not-run on main and green on branch: **62**. Regressions (green on main, not green on branch): **0**.

| Area | Case | main | branch |
|---|---|---|---|
| SKILL | canonical skill package passes --strict | FAIL | PASS |
| SKILL | gate hostile H03-paraphrase | FAIL | PASS |
| SKILL | gate hostile H04-unicode-tags | FAIL | PASS |
| SKILL | gate hostile H06-env-exfil | FAIL | PASS |
| SKILL | gate hostile H09-html-comment | FAIL | PASS |
| SKILL | gate hostile H10-concat | FAIL | PASS |
| SKILL | gate hostile H11-homoglyph | FAIL | PASS |
| SKILL | gate hostile H12-json-directive | FAIL | PASS |
| SKILL | gate hostile H14-trigger-hijack | FAIL | PASS |
| SKILL | gate hostile H16-getattr | FAIL | PASS |
| SKILL | hostile skills approved (total) | FAIL | PASS |
| SKILL | skills/ root is not a skill package | FAIL | PASS |
| SKILL | structure+referential integrity | FAIL | PASS |
| MCP | gate mcp PATH: evade | FAIL | PASS |
| MCP | gate mcp PATH: py_clean | FAIL | PASS |
| MCP | gate mcp PATH: ts_vuln | FAIL | PASS |
| MCP | gate mcp URL: poisoned+gamed fails CI | FAIL | PASS |
| MCP | knowledge server HTTP: 401 unauth, 200 auth | FAIL | PASS |
| MCP | knowledge server: imports after documented install | FAIL | PASS |
| MCP | score: cites v3.1 profile | FAIL | PASS |
| MCP | score: grade-gaming poisoned server | FAIL | PASS |
| MCP | score: honest server outranks poisoned | FAIL | PASS |
| MCP | score: self-attestation adds no points | FAIL | PASS |
| MCP | wrap audit attributes tool/method | FAIL | PASS |
| MCP | wrap-proxy --pin-schema: rug pull withheld | FAIL | PASS |
| MCP | wrap-stdio --block: payload not delivered | FAIL | PASS |
| MCP | wrap-stdio: client EOF terminates wrapper | FAIL | PASS |
| CLI | gate-project-vuln-Tier2 | FAIL | PASS |
| NEXUS | CI runs OPA on NEXUS/opa | FAIL | PASS |
| NEXUS | OPA 0.65 (compose pin): policies compile | FAIL | PASS |
| NEXUS | OPA 1.x: opa test | FAIL | PASS |
| NEXUS | OPA 1.x: policies compile (--strict) | FAIL | PASS |
| NEXUS | agbom: changed digest not silently trusted | FAIL | PASS |
| NEXUS | agbom: historical snapshot isolated from live edits | FAIL | PASS |
| NEXUS | agbom: manifest digest change surfaced (rug pull) | FAIL | PASS |
| NEXUS | agbom: tampered historical component detected | FAIL | PASS |
| NEXUS | agbom: tampered latest component detected | FAIL | PASS |
| NEXUS | compose OPA mount resolves to the policies | FAIL | PASS |
| NEXUS | guardian: ACT-4 reasoning='x' | FAIL | PASS |
| NEXUS | guardian: GCP metadata host | FAIL | PASS |
| NEXUS | guardian: IMDS IPv6 | FAIL | PASS |
| NEXUS | guardian: IMDS decimal IP | FAIL | PASS |
| NEXUS | guardian: IMDS hex IP | FAIL | PASS |
| NEXUS | guardian: aws creds file | FAIL | PASS |
| NEXUS | guardian: benign search, tier omitted | FAIL | PASS |
| NEXUS | guardian: double slash //etc//passwd | FAIL | PASS |
| NEXUS | guardian: id_ed25519 key | FAIL | PASS |
| NEXUS | guardian: kube config | FAIL | PASS |
| NEXUS | guardian: pipe to shell | FAIL | PASS |
| NEXUS | guardian: private key in arg | FAIL | PASS |
| NEXUS | guardian: single ../ | FAIL | PASS |
| NEXUS | guardian: tier omitted (None) | FAIL | PASS |
| NEXUS | guardian: url-encoded traversal | FAIL | PASS |
| NEXUS | guardian: windows backslash | FAIL | PASS |
| NEXUS | nexus-score claims agree with battery evidence | FAIL | PASS |
| NEXUS | opa: baseline capability allowed | FAIL | PASS |
| NEXUS | opa: config_change ACT-2 with approval allowed | FAIL | PASS |
| NEXUS | opa: decision defined for every input | FAIL | PASS |
| NEXUS | opa: deny_reason explains a denial | FAIL | PASS |
| NEXUS | opa: evaluates on OPA 1.x | FAIL | PASS |
| NEXUS | opa: scope downgrade: PERMANENT zone + 'request' scope denied | FAIL | PASS |
| NEXUS | opa: unrecognized scope 'Durable ' w/o mandate denied | FAIL | PASS |
