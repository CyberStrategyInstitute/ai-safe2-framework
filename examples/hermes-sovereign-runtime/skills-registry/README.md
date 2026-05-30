# Sovereign Skills Registry
### Hermes Sovereign Runtime · AI SAFE² v3.0 · P2.A-C01 + P5.E-C05

---

## Why This Exists

The agentskills.io community hub for Hermes Agent is a supply chain attack surface.
Any skill published there executes as Python in your agent environment. "Top downloaded"
is not a safety signal — it's a targeting signal.

CSA's 2026 analysis found that 26% of community agent skills contained at least one
security vulnerability. The top-downloaded OpenClaw skill at one point was confirmed malware.

The Sovereign Skills Registry enforces a review gate before any skill enters the runtime.

---

## Review Process

Every skill entering the sovereign runtime must pass:

1. **Static analysis** — `scanner.py` finds dangerous patterns (subprocess, eval, credential paths)
2. **Code review** — Human reviewer reads the skill source
3. **Sandbox behavior analysis** — Skill runs in isolated environment; behavior logged
4. **Provenance manifest** — Source, reviewer, review date, SHA256 hash recorded
5. **Security lead approval** — Sign-off before installation

**Time estimate:** 30–60 minutes per skill. This is the correct cost.

---

## Adding a Skill

```bash
# 1. Download the skill to staging (NOT directly to ~/.hermes/skills/)
mkdir -p skills-registry/staging/
wget https://agentskills.io/skills/whatever.py -O skills-registry/staging/whatever.py

# 2. Run automated scan
python3 ../gateway/scanner.py --skills --target skills-registry/staging/ --strict
# Must pass with zero CRITICAL findings

# 3. Create provenance manifest
cp skills-registry/skill_manifest_template.yaml skills-registry/staging/whatever.manifest.yaml
# Fill in all fields — especially source URL, SHA256, and reviewer

# 4. Review source code manually
# Read every line. Look for: external URLs, subprocess, eval, credential paths, obfuscation

# 5. Run in sandbox (Docker with no network, no credentials)
docker run --rm --network none -v $(pwd)/skills-registry/staging:/skills python:3.12-slim \
  python3 /skills/whatever.py 2>&1 | tee skills-registry/staging/whatever.sandbox.log

# 6. If review passes, move to approved/
mv skills-registry/staging/whatever.py skills-registry/approved/
mv skills-registry/staging/whatever.manifest.yaml skills-registry/approved/

# 7. Install to Hermes
cp skills-registry/approved/whatever.py ~/.hermes/skills/
```

---

## Skill Manifest Template

See `skill_manifest_template.yaml` for the full provenance record format.

Required fields:
- `skill_name` — canonical name
- `source_url` — where it came from
- `sha256` — hash of the skill file (verify with `sha256sum skill.py`)
- `reviewed_by` — reviewer name/handle
- `reviewed_at` — ISO 8601 timestamp
- `sandbox_tested` — true/false
- `static_scan_passed` — true/false
- `approved_by` — security lead name
- `approved_at` — ISO 8601 timestamp

---

## Approved Skills Directory

Skills in `approved/` have passed the full review process.
Each skill has a corresponding `.manifest.yaml` provenance record.

The Docker Compose stack mounts `hermes-skills` volume which maps to approved skills:
```yaml
volumes:
  - hermes-skills:/home/hermes/.hermes/skills
```

Populate the `hermes-skills` volume with approved skills before first run.

---

*Sovereign Skills Registry · Cyber Strategy Institute · AI SAFE² v3.0*
