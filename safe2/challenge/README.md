# AI SAFE² Challenge Evidence Runtime

Offline fixture experiments, provider-neutral translation, and reproducible grading.

[![AI SAFE²](https://img.shields.io/badge/AI_SAFE%C2%B2-v3.1-F6921E?style=flat-square)](../../README.md)
[![Module](https://img.shields.io/badge/Module-Challenge_Evidence-820F1A?style=flat-square)](../../docs/CHALLENGE-CLI.md)

[Framework Home](../../README.md) | [Cross-Pillar Governance](../../00-cross-pillar/README.md) | [AISM](../../AISM/) | [NEXUS](../../NEXUS/) | [Dashboard](https://cyberstrategyinstitute.github.io/ai-safe2-framework/dashboard/)

---

Start with the [command reference and runnable workflow](../../docs/CHALLENGE-CLI.md).
The [design contract](../../docs/CHALLENGE-HARNESS-DESIGN.md) explains the wire format.
The [Challenge Lab](../../challenges/) owns study protocols and evidence standards;
this directory is the installable Python implementation, not a separate framework.

| Module | Responsibility |
|---|---|
| `protocol.py`, `runner.py` | Pin the six-case protocol and run three inert fixture treatments |
| `bundle.py` | Orchestrate the one-command starter and verify portable bundles without executing submitted code |
| `grading.py` | Recompute state-based outcomes without accepting producer scores |
| `adapters.py` | Translate generic or illustrative TENIR exports, preserving originals |
| `compare.py` | Refuse incompatible conditions and expose agreement, gaps, and conflicts |
| `model.py`, `integrity.py` | Validate evidence semantics, detect changes, and verify optional signatures |
| `io.py` | Bound local artifact I/O and reject unsafe paths and overwrites |
| `report.py` | Render human-readable Markdown and self-contained HTML Decision Cards |

No live agents or provider code are executed. Synthetic translation agreement is
not independent replication. Framework conformance and AISM maturity remain
unassessed; real deployments require the Lab's separate live-evidence process.

---

*AI SAFE² v3.1 · [Cyber Strategy Institute](https://cyberstrategyinstitute.com/ai-safe2/)*
