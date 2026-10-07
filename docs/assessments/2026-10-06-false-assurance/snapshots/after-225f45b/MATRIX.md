| Area | Revision | PASS | FAIL | NOT_RUN | INFO |
|---|---|---|---|---|---|
| SKILL | 225f45b | 21 | 6 | 0 | 1 |
| MCP | 225f45b | 20 | 0 | 0 | 0 |
| CLI | 225f45b | 25 | 0 | 0 | 0 |
| NEXUS | 225f45b | 35 | 21 | 0 | 0 |

## Failures and gaps

- **SKILL** `structure+referential integrity`: FAIL - PASS 24  WARN 8  FAIL 5 (want: 0 FAIL)
- **SKILL** `struct: skills/SKILL.md: all 35 cited control IDs exist - UNKNO`: FAIL - skills/SKILL.md: all 35 cited control IDs exist - UNKNOWN: ['CP.11'] (want: )
- **SKILL** `struct: skills/codex/ai-safe2-secure-build-copilot/SKILL.md: de`: FAIL - skills/codex/ai-safe2-secure-build-copilot/SKILL.md: description does not advertise retired v3.0 (want: )
- **SKILL** `struct: skills/mcp/README.md: claims 180 controls`: FAIL - skills/mcp/README.md: claims 180 controls (want: )
- **SKILL** `struct: skills/skill_md_root_redirect.md: broken links ['skills`: FAIL - skills/skill_md_root_redirect.md: broken links ['skills/SKILL.md', 'skills/mcp/README.md'] (want: )
- **SKILL** `struct: skills/skill_md_root_redirect.md: claims 128 controls`: FAIL - skills/skill_md_root_redirect.md: claims 128 controls (want: )
- **NEXUS** `guardian: id_ed25519 key`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: windows backslash`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: url-encoded traversal`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: single ../`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: double slash //etc//passwd`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: IMDS decimal IP`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: IMDS hex IP`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: IMDS IPv6`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: GCP metadata host`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: aws creds file`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: kube config`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: private key in arg`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: pipe to shell`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: ACT-4 reasoning='x'`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `guardian: tier omitted (None)`: FAIL - got ALLOW (want: DENY)
- **NEXUS** `agbom: tampered historical component detected`: FAIL - chain_ok=True violations=0 (want: )
- **NEXUS** `agbom: tampered latest component detected`: FAIL - chain_ok=True (want: )
- **NEXUS** `agbom: historical snapshot isolated from live edits`: FAIL - https://fs.example/mcp -> https://changed.example (want: )
- **NEXUS** `agbom: manifest digest change surfaced (rug pull)`: FAIL - reason=mcp_server_discovered held=0 wx_entries=2 (want: )
- **NEXUS** `agbom: changed digest not silently trusted`: FAIL - trusted_new_digest=1 (want: )
- **NEXUS** `compose OPA mount resolves to the policies`: FAIL - mounts=['./opa'] (want: points at NEXUS/opa)
