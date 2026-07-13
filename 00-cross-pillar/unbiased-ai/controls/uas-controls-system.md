# UAS System-Side Controls (14) | AI SAFE² Sourced
| ID | Control | Primary source | Test method |
|---|---|---|---|
| UAS-S1 | Factual claim source attribution | P2, P4 | RAG audit trace |
| UAS-S2 | Political neutrality probe testing | P5 eval gates | Matched-pair benchmark suite |
| UAS-S3 | Commercial interest filtering | P1 isolation | Sponsored content detection |
| UAS-S4 | Behavioral drift baseline enforcement | P3 | Drift delta scoring |
| UAS-S5 | Adversarial framing resistance | P1 fuzzing | Red-team scenario catalog |
| UAS-S6 | Model routing decision audit | P4, NEXUS | Routing trace log review |
| UAS-S7 | RAG retrieval bias detection | P2 lineage | Corpus representativeness audit |
| UAS-S8 | Fine-tuning contamination screening | CP.8 lineage | SHA-verified lineage review |
| UAS-S9 | Output consistency across demographic prompts | P4, P5 | Demographic parity testing |
| UAS-S10 | System prompt immutability audit | P1, NEXUS | Injection resistance test |
| UAS-S11 | Emotional priming detection | P4 behavioral | Sentiment trajectory analysis |
| UAS-S12 | Authority simulation resistance | P1 cognitive isolation | Social engineering probe |
| UAS-S13 | Historical accuracy validation | P5 eval gates | Verified fact corpus testing |
| UAS-S14 | Cross-session influence tracking | NEXUS memory governance | Session delta analysis |

## Addendum: UAS-S15 (v1.1)
| ID | Control | Primary source | Test method |
|---|---|---|---|
| UAS-S15 | Jurisdictional grounding of legal and policy outputs | P5 eval gates, P2 attribution | US controlling-authority corpus test (Test 8) |

UAS-S15 requires that, for the Government-configured deployment, model responses to questions of law, regulation, policy, or compliance posed by Government users are grounded in controlling US legal authority in hierarchical order: the Constitution, ratified treaties, federal statutes, regulations, executive orders, and agency guidance. Foreign and international instruments (foreign statutes, non-ratified conventions, standards bodies, intergovernmental fora) may be presented as comparative or persuasive material only when identified as such, never silently substituted as the operative frame. Misgrounded answers are truthfulness defects under (j)(1)(i), not viewpoint violations; the control tests accuracy against controlling authority, not ideological alignment.
