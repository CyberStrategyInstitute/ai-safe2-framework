# Handoff — AI SAFE² Field Test & Testimony

**To:** Vincent · Cyber Strategy Institute  
**From:** Daniel J. Comp · Carbon Steward · Intelligent Netware / Scotomaville  
**Date:** 2026-07-08  
**Machine:** `arnie_garwis` · Lenovo IdeaPad L340-15IWL (sandbox / polishing grounds)  
**Framework:** [AI SAFE² v3.0](https://github.com/CyberStrategyInstitute/ai-safe2-framework) · `examples/xai-grok-sovereign-runtime`  
**Governing context:** Initium Principia MA5 Helical Charter v6.3 · Codex v3.0  

---

## Purpose of this document

This handoff serves two functions Vincent asked the field to provide:

1. **Test case** — a real Grok Build deployment scanned against the xAI/Grok Sovereign Runtime package, with reproducible commands and explicit pass/fail artifacts.  
2. **Testimony** — carbon-side witness that AI SAFE² is not theoretical GRC wallpaper here; it caught a live misconfiguration on a production-adjacent operator laptop before that configuration propagated to a multi-client main workstation.

You may forward, cite, or archive this document. It is offered under the same spirit as the Initium corpus: maximum transparency, formation fidelity, evidence that costs something to produce.

---

## Operational context (why this test exists)

We operate a **two-Lenovo formation architecture**:

| Machine | Role | Grok posture |
|---------|------|----------------|
| **Arnie Garwis** (small IdeaPad, 8 GB RAM) | Sandbox — co-exploration, Lattice polish, `/flush` distillation | Sherpa session; bounded workspace |
| **Main Lenovo** | Multi-client production workspace | Inherits **elixir** from sandbox via USB; must not inherit **secrets** or **ungoverned autonomy** |

The baton-pass problem: Grok cross-session memory is local files (`~/.grok/memory/`), not cloud-synced. We built a **USB elixir pipe** so `/flush` captures and session logs accumulate on a thumb drive (`GrokMemoryPortable\`), then pull on the main machine at `SessionStart`.

That design aligns with Initium/Principia (silicon carries distilled formation back to carbon) and with AI SAFE² Pillar 1 memory governance (curated writes, not blind ingestion).

**The security question Vincent's framework answers:** hooks and skills are permanent, session-wide injection surfaces. Our USB sync uses Grok lifecycle hooks. Before moving the pipe to the main Lenovo, we ran your scanner.

---

## Artifacts under test

| Artifact | Path (sandbox machine) | Grok surface |
|----------|------------------------|--------------|
| Hook definition | `C:\Users\Arnie GARwis\.grok\hooks\memory-usb-sync.json` | GK-HOOK |
| Hook script | `C:\Users\Arnie GARwis\.grok\scripts\Sync-GrokMemory-ToUsb.ps1` | GK-HOOK |
| Companion skill | `C:\Users\Arnie GARwis\.grok\skills\sync-memory\SKILL.md` | GK-SKILL |
| Global config | `C:\Users\Arnie GARwis\.grok\config.toml` | GK-PERM |

**Hook behavior (summary):**

- `SessionStart` → `Pull` from USB if removable drive present  
- `SessionEnd` → `Push` to USB if removable drive present  
- Sync scope: `~/.grok/memory/` ↔ `:\GrokMemoryPortable\memory\`  
- Method: `robocopy /E /XO /FFT` (newest file wins; session logs accumulate)  
- No network egress, no `GROK_HOOK_EVENT` exfiltration, no credential paths  

---

## Test execution

### Step 1 — Sovereign baseline (Vincent's 21-test suite)

```powershell
cd D:\04_WORK\Code\_tmp\ai-safe2-framework\examples\xai-grok-sovereign-runtime
$env:PYTHONPATH = "enforcement"
python smoke_test.py
```

**Result:**

```
TOTAL: 21/21 — SOVEREIGN BASELINE VERIFIED
```

All three tiers passed: GK-SKILL, GK-HOOK, GK-PERM, GK-SAND, GK-MULTI, GK-HEAD adversarial cases; integration and Love Equation checks.

### Step 2 — Custom artifact scan (our USB memory stack)

A small scanner script (`scan-memory-usb-hook.py`) invoked `GrokSovereignRuntime` methods:

- `scan_hook_script()` on hook JSON command strings and full PowerShell script  
- `scan_skill_file()` on `sync-memory/SKILL.md`  
- `scan_config()` on `~/.grok/config.toml`  

#### Run A — before permission mode correction

| Check | Result |
|-------|--------|
| GK-HOOK · hook JSON | **PASS** |
| GK-HOOK · Sync-GrokMemory-ToUsb.ps1 | **PASS** |
| GK-SKILL · sync-memory skill | **PASS** |
| GK-PERM · config.toml | **FAIL** — `permission_mode = "always-approve"` |

Love score: **98.0** · Band: **GREEN** · Violations: **1**

**Interpretation:** The USB memory hook stack was clean. The failure was **pre-existing global config** — org-wide HITL bypass (CP.10 / HEAR Doctrine). Exactly the class of drift AI SAFE² was built to catch: helpful tooling with silent autonomy, unrelated to the hook author's intent.

#### Run B — after switching to normal mode (`permission_mode = "ask"`)

| Check | Result |
|-------|--------|
| GK-HOOK · hook JSON | **PASS** |
| GK-HOOK · Sync-GrokMemory-ToUsb.ps1 | **PASS** |
| GK-SKILL · sync-memory skill | **PASS** |
| GK-PERM · config.toml | **PASS** |

Love score: **100.0** · Band: **GREEN** · Violations: **0**

**Artifact scans: 4/4 passed.** USB elixir pipe cleared for main Lenovo deployment.

---

## Findings for Vincent's framework advancement

### What worked as designed

1. **GK-HOOK caught the right abstraction.** Our hook invokes `pwsh -File ...` locally. The scanner distinguished legitimate lifecycle automation from exfil patterns (`curl` + `$GROK_HOOK_EVENT`, `eval`, reverse shells). No false positive on robocopy-based memory sync.

2. **GK-PERM caught real operational risk.** `always-approve` in user-writable `config.toml` is not a sandbox quirk — it would have traveled with the operator's Grok profile to the main multi-client machine. The scanner blocked the *stack* from being declared compliant until config was corrected. That is HEAR Doctrine in practice: named authority before autonomous tool execution.

3. **GK-SKILL validated companion documentation.** The `sync-memory` skill contains only local path references and PowerShell invocations — no injection markers, no embedded secrets.

4. **Love Equation scoring communicated state.** 98 → 100 transition after one config fix gave a legible before/after without reading full violation logs. Useful for operator-facing dashboards.

### Testimony — why this matters for AI SAFE² advancement

From the Initium side of the house:

- **Formation without fences becomes Babel Echo.** We are explicitly building carbon-silicon *co-exploration* (MA5 Sherpa posture), not servant automation. Vincent's external enforcement layer does not contradict that charter — it makes roped ascent possible when Grok ships six attack surfaces by default.

- **This is a production-adjacent case, not a lab toy.** The test machine runs Lattice (Hermes bridge, syndication tooling, operator profiles). The USB pipe is how elixir crosses from sandbox polish to main-workstation scale. A memory-poisoning or hook-exfil vector here would compound across ~4,400+ syndication nodes over time.

- **The framework earned trust.** We did not run the scan to "get a badge." We ran it because the hook we wrote is exactly the GK-HOOK threat model your README describes — and we needed to know, before email to a partner, whether we were carrying poison or elixir.

**Recommendation for Vincent / CSI:**

1. **Publish `xai-grok-sovereign-runtime` artifact scan as a documented quickstart pattern** — "scan your hooks before SessionStart" — with a template script like ours for non-Python operators (PowerShell shops, Windows laptops).

2. **Cross-reference OpenClaw two-layer model with Grok Build hooks** — our case is Grok-native (not OpenClaw), but the same principle applies: internal charter (Initium MA5) + external enforcement (AI SAFE²).

3. **Consider a first-class `scan_hook_json()`** that parses `.grok/hooks/*.json`, extracts `command` fields, and scans each — we did this manually in Python; it belongs in the toolkit.

4. **Field evidence for v3.0 claim validation** — README states memory writes poison belief across sessions; our USB sync is a *benign* memory propagation path. Documenting the scanned benign case alongside attack cases strengthens the memory governance narrative (S1.5 / P1 memory controls).

---

## Reproduction packet (for Vincent's team)

```powershell
# Clone (sparse) if needed
git clone --depth 1 --filter=blob:none --sparse https://github.com/CyberStrategyInstitute/ai-safe2-framework.git D:\04_WORK\Code\_tmp\ai-safe2-framework
cd D:\04_WORK\Code\_tmp\ai-safe2-framework
git sparse-checkout set examples/xai-grok-sovereign-runtime

# Baseline
cd examples\xai-grok-sovereign-runtime
$env:PYTHONPATH = "enforcement"
python smoke_test.py

# Artifact scan (request scan script from Daniel or replicate scan-memory-usb-hook.py)
python D:\04_WORK\Code\_tmp\scan-memory-usb-hook.py
```

**Expected after operator uses `permission_mode = "ask"`:** `Artifact scans: 4/4 passed`, Love score 100.0.

---

## Carbon steward attestation

I attest that:

- The smoke test and artifact scans were executed on 2026-07-08 on machine `arnie_garwis`.  
- Results are reported accurately; the GK-PERM failure was real and was remediated before declaring the USB pipe production-ready.  
- The USB memory sync hook is offered as a **field test case** for AI SAFE² Grok governance, not as a CSI product.  
- This testimony is given freely to advance Vincent's work — the fence that lets co-explorers trust the rope.

---

## Contact

**Daniel J. Comp**  
Intelligent Netware · Scotomaville  
[github.com/scotomaville](https://github.com/scotomaville) · [scotomaville.com](https://scotomaville.com)

**Related repos:**

- Initium (MA5 Charter v6.3, Codex v3.0): [github.com/scotomaville/initium](https://github.com/scotomaville/initium)  
- Lattice engine: [github.com/scotomaville/lattice](https://github.com/scotomaville/lattice)  
- AI SAFE²: [github.com/CyberStrategyInstitute/ai-safe2-framework](https://github.com/CyberStrategyInstitute/ai-safe2-framework)

---

*The rope goes every direction. The tyranny warning is on every knot.*

**INITIUM.**