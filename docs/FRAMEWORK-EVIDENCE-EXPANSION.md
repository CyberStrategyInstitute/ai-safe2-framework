# Evidence expansion and adversarial review

Review date November 19, 2026. This addendum supersedes the earlier plan wherever that plan narrows a candidate now promoted below. It records three distinct reasoning passes performed by the same assistant: evidence recovery, adversarial challenge, and reconsideration of excluded material. These passes provide a structured self-review. Independent reviewer evidence remains a separate requirement for comparative effectiveness claims.

## Revised recommendation

Carry 52 individually reviewable decisions into the full framework update. The original 32 decisions remain, with the 20 additions below expanding or sharpening their objectives. Twelve standalone controls are now proposed in total, comprising the original six candidates and six additional candidates C33-C38. This would yield 173 core controls if all twelve are adopted without consolidation or retirement. That arithmetic describes the proposal. Canonical numbering and the final count follow the actual approved requirements. There is no target ceiling on controls, sub-controls, profiles or research notes.

The 20 additions contain 83 explicit draft child requirements. These clauses describe what must be written and tested. Some make an earlier broad objective precise. They are not 83 new core controls, and the total number of required child clauses across the full update remains open. Six profile workstreams remain, with C40 expanding browser/personal-agent coverage to separate computer-use and browser treatments. The accompanying research register adds 20 individually scoped note proposals to the research work already required for C01-C32. New note versus substantive revision follows source ownership and the research question, with no numerical cap.

Keep the Rosetta Stone purpose visible. An organization should translate a regulatory or assurance question into applicable AI SAFE2 requirements, implementation checks, failure evidence and a repair path, then trace the result back to the original source. An agent should be able to perform the same translation with canonical IDs and explicit scope. Comparable evidence can be reused where the individual obligations permit it. Distinct or partially met obligations remain visible.

## Pass 1 - Recovery audit and missed opportunities

All four supplied recovery files were read in full and their CSV records enumerated. The supplied framework register has 32 entries. The control-link file has 496 unique recorded tag/control pairs covering all 161 core controls. Of these, 495 use external-framework labels and one uses the internal reference E5.1_linked, explicitly marked in the recovery file as an unregistered value rather than an external framework. Remove that internal link from external-framework coverage arithmetic and preserve it as a control dependency. The clause-crosswalk file has 706 recorded cells covering 129 AI SAFE2 subtopics and seven framework IDs. Counts in the 32-row register reconcile to those two files for each listed framework. These counts describe recovered records, with no assertion of verified external-clause coverage.

| Recorded crosswalk family | Cells |
| --- | ---: |
| NIST AI RMF | 129 |
| ISO/IEC 42001 | 129 |
| CSA AICM | 129 |
| NIST CSF | 129 |
| EU AI Act | 128 |
| OWASP LLM Top 10 | 36 |
| MITRE ATLAS | 26 |

CSA AICM appears in the clause crosswalk but has no row in the 32-framework register and no tag in the supplied control-link file. Reconcile it as an additional source-family record before computing any unified coverage denominator. Framework labels overlap in purpose and vary in authority. Thirty-three external source-family dispositions plus the separately identified internal-tag anomaly describe these files, and that number does not mean 33 validated compliance mappings.

The extracts preserve historical percentages, approximate clauses and generalized locators such as Full ATLAS mapping. They also preserve a research claim of approximately 40 percent reduced compliance overhead. The recovered files supply no measurement protocol for that reduction. Retain the historical attribution and seek its supporting benchmark before reuse. Validate each edition and individual locator. In particular, the historical extracts contain ISO/IEC 42001:2022 references while the published standard is ISO/IEC 42001:2023. Register the NIST Generative AI Profile separately from AI RMF. [ISO edition](https://www.iso.org/standard/42001) · [NIST AI 600-1](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)

The original research supplied several findings that the earlier plan underused: design-time multi-agent coordination, environment identity, idempotent effects, completion verification, success criteria, failure location, memory validity, rights and participation, fairness methods, portfolio dependencies, and proportional adoption. The source's JEV scores and failure percentages were analyst judgments or cited study results with bounded scope. They identify useful questions and candidate tests. Each operational or prevalence claim still needs its own primary-source verification and denominator. The plan must preserve that nuance while adopting warranted engineering requirements.

## Individually promoted or deepened requirements

Review IDs below are temporary planning identities. Each child requirement also has a stable review locator. A parent-control absorption is valid only when the parent gains the normative depth, applicability, implementation boundary, tests, recovery and research rationale described here.


<a id="c33"></a>

### C33 Design-time coordination contract

**Recommendation** Add standalone cross-pillar control.

**Source** Wave 04 Holds, Proposed for v3.2; Wave 02 shared-resource and swarm requirements.

**Why and trade-off** C14 handles combined authorization and C23 handles voting. Neither requires roles, ownership or termination to be defined before a workflow starts. Independent design acceptance has its own lifecycle. Extra specification effort can slow prototyping; permit declared exploratory scope with bounded effects.

**Draft requirements**

- **C33.1** Declare role responsibilities, allowed interactions, authoritative shared resources and accountable owner before consequential deployment.
- **C33.2** Define completion, cancellation, termination and conflict-resolution conditions for the task graph.
- **C33.3** Validate handoffs, cyclic dependencies, abandoned locks and competing writers before promotion.
- **C33.4** Bind the approved coordination version to execution and revalidate changes in membership or role authority.

**Corresponding research note** Coordination before execution. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Show that an allowed but contradictory set of roles is rejected before deployment; a valid graph can complete. Retain synthetic fixtures and source-specific study limitations. The supplied 79% figure needs its own primary-study denominator and applicability review.


<a id="c34"></a>

### C34 Environment-bound authority

**Recommendation** Add standalone P3 control.

**Source** Wave 04 Holds, Environment Binding and Assertion; Wave 02 purpose separation.

**Why and trade-off** Isolation alone does not establish which environment an authorized action targets. A distinct effect gate makes production/development assertions independently testable. Environment identity management and emergency procedures add operational cost.

**Draft requirements**

- **C34.1** Bind action authority to a verified environment, tenant and resource identity.
- **C34.2** Require an independently issued environment assertion for destructive or material operations.
- **C34.3** Refuse a mismatched, expired or unknown environment assertion and prevent agent self-issuance.
- **C34.4** Revalidate after a route, account, region, resource alias or environment change.

**Corresponding research note** Environment identity and destructive actions. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Run synthetic development/production twins and verify that changed endpoint or account cannot redirect an approval. Validate the cited incidents individually before attributing their causes.


<a id="c35"></a>

### C35 Idempotency and side-effect ledger

**Recommendation** Add standalone P3 control with P2 evidence.

**Source** Wave 04 Holds, Idempotency and Side-Effect Ledger; Wave 02 ASG-13 and transactions.

**Why and trade-off** C18 compressed ledger semantics into general transaction safety. Reservation, commitment and unknown outcomes warrant an explicit reusable requirement. P2 records evidence; the P3 mechanism prevents duplicate effects. Central state adds collision and availability risks.

**Draft requirements**

- **C35.1** Bind each idempotency key to task, operation, destination and canonical action parameters.
- **C35.2** Reserve and commit the operation atomically where supported; reject key reuse for a different action.
- **C35.3** Reconcile ambiguous results against destination state before retrying an irreversible effect.
- **C35.4** Define retention, collision handling, timeout, partial completion and compensation semantics.
- **C35.5** Return the recorded result for a completed identical request without executing it again.

**Corresponding research note** Idempotency, ambiguity and settlement. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Exercise concurrent duplicate requests, key collision, timeout after commit and ledger outage. Document external services where exact duplicate suppression cannot be established.


<a id="c36"></a>

### C36 Verified outcome contract

**Recommendation** Add standalone P2 control.

**Source** Wave 04 Holds, Post-Condition Verification; Wave 02 P2-01; merged CI receipt boundary.

**Why and trade-off** C04 concerns evidence independence across claims. This objective defines completion itself. Existing receipt tooling does not make an external business outcome verified. Additional observations can add latency and expose sensitive state.

**Draft requirements**

- **C36.1** Declare the external postcondition and its authoritative observation method.
- **C36.2** Distinguish attempted, accepted, committed, independently verified, failed and unknown outcomes.
- **C36.3** Bind the observation to the action, target, revision and observation time.
- **C36.4** Prevent a tool success response or agent completion message from alone satisfying the postcondition.
- **C36.5** Scope verification frequency and retention to consequence and preserve unknown coverage.

**Corresponding research note** Completion versus independently verified effect. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Return HTTP success without the intended state change, then mutate the wrong target. Both remain incomplete or failed. Include legitimate success and an unavailable observer.


<a id="c37"></a>

### C37 Declared success and acceptance criteria

**Recommendation** Add standalone P5 control.

**Source** Wave 04 Holds, Declared Success Criteria Gate; Wave 02 G-01 and P5 requirements.

**Why and trade-off** Evaluation cadence cannot compensate for a missing task objective. This gate applies at design and acceptance time, while C36 applies after execution. Exploratory and qualitative work need explicit human review criteria instead of fabricated machine precision.

**Draft requirements**

- **C37.1** Declare intended benefit, observable success, prohibited effects and accepted uncertainty before consequential operation.
- **C37.2** Use executable assertions where feasible and identify the responsible human rubric when judgment remains necessary.
- **C37.3** Bind criteria to the workflow version and prevent the acting agent from relaxing them after observing its result.
- **C37.4** Keep task completion, safety, utility and cost as separate outcomes.

**Corresponding research note** Success criteria and useful work. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Demonstrate that a workflow with no criteria cannot claim validated completion. Test correct assistance, safe refusal, false blocking and an approved exploratory task. Recheck the source of the supplied 41% figure.


<a id="c38"></a>

### C38 Evidence-based failure attribution

**Recommendation** Add standalone P2 control.

**Source** Wave 04 Holds, Failure Location; Developer Workflow CI execution receipt; Wave 02 outcome evidence.

**Why and trade-off** Observed failure location and causal root cause are different claims. Existing CI phase classification provides a bounded implementation to generalize. A distinct requirement makes repair guidance testable. Evidence collection can be incomplete and causality may remain unresolved.

**Draft requirements**

- **C38.1** Record failures by environment, build, transport, harness, application, postprocessing, publication and applicable runtime boundary.
- **C38.2** Attach observations, competing explanations and unavailable evidence to each proposed failure location.
- **C38.3** Keep ranked hypotheses distinct from verified causes and explicit unknown states.
- **C38.4** Link each accepted diagnosis to a repair and a repeat of the relevant failing case.

**Corresponding research note** Failure attribution and repair evidence. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** A passing application test followed by a broken wrapper must retain both observations. Compare diagnoses with an independently labeled synthetic fault set before claiming superiority over published work.


<a id="c39"></a>

### C39 Outcome-aware memory and correction precedence

**Recommendation** Add explicit C13 child requirements.

**Source** Wave 04 Holds, Memory Outcome Annotation; Wave 02 derived-state laundering.

**Why and trade-off** Expiry and provenance describe origin and lifetime. They do not establish whether an entry is failed or superseded. Reuse the memory lifecycle while making validity independently queryable. Incorrect corrections can suppress useful knowledge.

**Draft requirements**

- **C39.1** Attach verified, failed, disputed, superseded or unknown outcome status to reusable artifacts and durable entries.
- **C39.2** Preserve correction links, original evidence and reason for status changes.
- **C39.3** Retrieval must surface an applicable correction with the original claim and block superseded instructions from silently regaining authority.
- **C39.4** Carry correction state through summarization, export, replica restore and derivative generation.

**Corresponding research note** Memory validity and correction propagation. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Poison a synthetic entry, correct it, then retrieve its summary and restore its backup. Test erroneous correction reversal with accountable review.


<a id="c40"></a>

### C40 Computer-use state and verification

**Recommendation** Expand C28 into CUA and browser child profiles.

**Source** Wave 04 Holds, CP.5.CUA; Wave 01 Google Home specificity.

**Why and trade-off** Browser interfaces and native apps have distinct observation and action semantics. A browser-only profile loses native computer-use evidence. Shared final-effect controls remain inherited. Image and accessibility observations can be incomplete.

**Draft requirements**

- **C40.1** Record target application, account, document or page identity and relevant state before a material action.
- **C40.2** Require an observation fresh enough to identify the intended control and handle asynchronous state changes.
- **C40.3** Recheck the target after focus, navigation, layout, modal or account changes.
- **C40.4** Verify the resulting application or business state independently of the click or screenshot.
- **C40.5** Declare unsupported surfaces and evidence limitations; keep native-app and browser fixtures distinct.

**Corresponding research note** Computer-use authority and UI state. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Exercise stale screenshots, delayed page state, changed window focus, modal interception and a click that leaves the postcondition unmet. Preserve the source DOM-settle proposal as browser-specific treatment.


<a id="c41"></a>

### C41 Fairness, decision validity and accessibility

**Recommendation** Add explicit C07/C24 and UAS child requirements.

**Source** Wave 02 governance/fairness; Wave 06 rubric C13 and source crosswalk.

**Why and trade-off** Security and valid authority can coexist with invalid or unfair decisions. Existing impact and oversight homes need explicit statistical and accessibility requirements. Context-specific metrics and conflicting objectives require recorded choices.

**Draft requirements**

- **C41.1** Declare decision validity, affected populations, accessibility needs and task-specific fairness objectives.
- **C41.2** Record sample size, power rationale where applicable, effect sizes, uncertainty and subgroup limitations.
- **C41.3** Distinguish nonsignificant results from established absence of harmful disparities.
- **C41.4** Define mitigation that can change the decision, use restrictions or deployment and monitor its outcome.

**Corresponding research note** Fairness and valid decisions under authorized execution. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Evaluate authorized decisions that are systematically wrong or inaccessible. A mitigation must change relevant outcomes. Keep legal applicability and CSI-defined numerical thresholds attributed separately.


<a id="c42"></a>

### C42 No-AI alternative and deployment necessity

**Recommendation** Add explicit C06/C07 child requirements.

**Source** Wave 02 divergent governance ideas; expanded external inventory.

**Why and trade-off** Purpose classification does not compare alternatives. A documented suitability decision keeps the framework useful for ordinary organizations. Assessment effort should be proportional to consequence.

**Draft requirements**

- **C42.1** Compare AI use with a simpler deterministic or human process where consequences warrant the decision.
- **C42.2** Record expected benefit, material uncertainty, residual harms and conditions for withdrawing AI.
- **C42.3** Declare the deployment owner and criteria for reassessment when benefits fail to materialize.

**Corresponding research note** AI necessity, alternatives and acceptable uncertainty. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Compare two equally successful workflows with different exposure and maintenance costs. Preserve the rationale for selecting or rejecting automation.


<a id="c43"></a>

### C43 Portfolio concentration and correlated failures

**Recommendation** Add explicit C17/CP.8 child requirements.

**Source** Wave 02 divergent governance ideas; swarm common-mode evidence.

**Why and trade-off** Per-deployment fallback and independent agent identities miss shared providers, models, policies and evaluators. A portfolio assessment extends existing continuity and threshold ownership. Independence can cost money and introduce operational complexity.

**Draft requirements**

- **C43.1** Inventory shared model, provider, route, identity, policy, dataset and evaluator dependencies across deployments.
- **C43.2** Assess correlated loss or defect scenarios and bound cumulative exposure.
- **C43.3** Exercise an approved alternative and document dependencies shared with the primary path.
- **C43.4** Review concentration after material acquisitions, migrations and new deployments.

**Corresponding research note** Concentration and common-mode containment. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Disable a shared policy or provider in a synthetic multi-deployment estate and measure which fallback paths are actually independent.


<a id="c44"></a>

### C44 Emergency exceptions and governance-agent limits

**Recommendation** Add explicit C06/C20 child requirements.

**Source** Wave 02 emergency powers, governance-agent authority and policy integrity.

**Why and trade-off** An exception can permanently defeat all otherwise correct controls. Existing ownership is appropriate if authority, expiry and monitoring become mandatory. Tight emergency rules can impede urgent recovery.

**Draft requirements**

- **C44.1** Bind exceptions to a named authority, scope, reason, expiry and compensating measures.
- **C44.2** Prevent an acting or governance agent from approving its own exceptions or extending their lifetime.
- **C44.3** Log use, require post-event review and verify restoration of normal policy.
- **C44.4** Define a tested emergency path for unavailable approvers with limited consequences.

**Corresponding research note** Emergency authority and exception persistence. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Exercise expired exceptions, approver outage and an agent requesting wider rights. Verify revocation and restoration after the emergency.


<a id="c45"></a>

### C45 Rights, retention and obligation conflicts

**Recommendation** Add explicit C19/C21/C22 child requirements.

**Source** Wave 02 IP/data rights and conflicting obligations; Wave 05 #390 and C11 redress.

**Why and trade-off** A source declaration does not resolve training rights, downstream reuse or a conflict between deletion and evidence retention. Add lifecycle-specific decisions and accountable conflict routing. This needs specialist applicability review.

**Draft requirements**

- **C45.1** Distinguish rights and policy decisions for training, retrieval, generation, publication and downstream reuse.
- **C45.2** Record declaration freshness, conflicting evidence and uncertainty without inferring permission from UNKNOWN.
- **C45.3** Route deletion, retention, security evidence and transparency conflicts to an accountable decision maker.
- **C45.4** Propagate approved correction/deletion decisions to applicable derived stores and record justified retention exceptions.

**Corresponding research note** Source rights through evidence retention and remedy. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Test contradictory declarations, a deletion request with a legitimate hold, and expired reuse permission. Report applicable scope and unresolved legal questions.


<a id="c46"></a>

### C46 Affected-party and worker participation

**Recommendation** Add explicit C07/C19/C24 child requirements.

**Source** Wave 02 worker/public participation; Wave 06 rubric contestability.

**Why and trade-off** Operator approval leaves bystanders, workers and affected populations unrepresented. Expand existing impact and remedy requirements with an explicit route for their evidence. Participation can raise privacy and representativeness problems.

**Draft requirements**

- **C46.1** Identify affected people absent from the operator approval chain.
- **C46.2** Collect proportionate input on impacts and accessibility and disclose its limitations.
- **C46.3** Provide an accessible route to challenge, correct or escalate material effects.
- **C46.4** Record whether input changed design, deployment, restrictions or remedy.

**Corresponding research note** Affected-party participation and practical redress. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Trace a complaint from a non-user through accountable review to an observed correction, retaining disagreement and safety constraints.


<a id="c47"></a>

### C47 Environmental and infrastructure resource impact

**Recommendation** Add explicit C05/C07 child requirements.

**Source** Wave 02 environmental/resource impacts; Wave 04 generalized consumable authority.

**Why and trade-off** Spend alone omits material compute, energy, water and infrastructure constraints. Add applicability-based measurement and limits. Precise measurement may be unavailable for hosted services.

**Draft requirements**

- **C47.1** Identify material infrastructure and environmental constraints for the deployment.
- **C47.2** Record measured, provider-reported, estimated and unknown resource use separately.
- **C47.3** Apply justified limits or procurement restrictions and recheck after scaling or model changes.

**Corresponding research note** Resource impacts beyond financial spend. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Compare measured use and estimates under a synthetic scaling scenario. Avoid turning uncertain estimates into exact environmental benefits.


<a id="c48"></a>

### C48 Assurer competence and conflict management

**Recommendation** Add explicit C04/C16/P5 child requirements.

**Source** Wave 02 assurer independence; Wave 06 rubric disagreement process.

**Why and trade-off** Independent custody alone cannot establish evaluator competence or representative tests. The evidence contract needs reviewer capability, conflicts and dispute handling. Independent review adds cost and may remain unavailable.

**Draft requirements**

- **C48.1** Record reviewer competence, tool scope, financial or organizational conflicts and access limits.
- **C48.2** Protect test selection, grader configuration and evidence custody from the evaluated agent.
- **C48.3** Preserve reviewer disagreement and its adjudication with traceable reasons.
- **C48.4** Retest after material changes to a benchmark, evaluator or assurance provider.

**Corresponding research note** Who validates the verifier. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Use a flawed grader, conflicted reviewer and contaminated test set. Verify that their verdict cannot silently become independent assurance.


<a id="c49"></a>

### C49 Threat intelligence linked to observed actor behavior

**Recommendation** Add explicit CP.6/CP.2/P4/P5 child requirements.

**Source** Wave 01 actors and operational developments; Wave 03 timelines and indicators.

**Why and trade-off** The plan emphasized mechanisms but did not require an operational intelligence product. Incident learning needs actor behavior, prerequisites and detection opportunities. Public attribution and prevalence can remain uncertain.

**Draft requirements**

- **C49.1** Record observed actions, entry points, prerequisites, effects and sources independently from actor attribution.
- **C49.2** Distinguish advisory, laboratory demonstration, observed exploitation and sustained operational activity.
- **C49.3** Link relevant techniques to detection, prevention, containment and regression cases with exact deployment scope.
- **C49.4** Preserve event, discovery, disclosure and fix dates, revisions, contradictions and confidence.
- **C49.5** Use evidence-driven update triggers and publish changes in source confidence without manufacturing population incident rates.

**Corresponding research note** Observed actor tradecraft and deployment relevance. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Turn one source-backed incident into a linked control/detection/test record and retain both the original disclosure and later correction. Forecasts carry falsifiers and remain distinct from recorded events.


<a id="c50"></a>

### C50 Proportional implementation and repair guidance

**Recommendation** Add explicit P5/P4 adoption child requirements.

**Source** Wave 04 Holds second-order effects and quickstart critique; Wave 02 small-organization profile.

**Why and trade-off** A control can be technically correct and routinely bypassed because it is unusable. Extend adoption and education with tested implementation paths. Simpler paths must retain consequence-based minimums.

**Draft requirements**

- **C50.1** Publish role-specific build, fix, defend and assess paths with applicable prerequisites.
- **C50.2** Provide a low-consequence local fixture before recommending customer-facing or production automation.
- **C50.3** Measure false blocks, completion, time to diagnose and recovery alongside safety outcomes.
- **C50.4** Offer accessible escalation and recovery instructions and declare unsupported environments.

**Corresponding research note** Adoption, operator burden and useful defense. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Have a new adopter complete a synthetic build/fix/defend exercise. Capture errors and burden, and verify that simplification does not remove applicable critical safeguards.


<a id="c51"></a>

### C51 Rosetta Stone source and relationship governance

**Recommendation** Add explicit C06/P2 mapping requirements.

**Source** All four mapping-recovery files; Wave 02 mapping schemas and retrieval contracts.

**Why and trade-off** The recovered 32 labels, 496 tags and 706 cells describe different levels of evidence. Preserve their lineage and deepen relationships. Mapping all controls to every framework creates false equivalence and maintenance cost.

**Draft requirements**

- **C51.1** Register publisher, edition, status, mapping units, role, jurisdiction, source locator and licensing constraints.
- **C51.2** Give each relationship a stable ID, direction, type, rationale, exclusions, reviewer and review date.
- **C51.3** Record unmapped, partially addressed, out-of-scope, disputed and unassessed dispositions explicitly.
- **C51.4** Derive reciprocal human and machine views from the same records and invalidate stale relationships after source or control changes.
- **C51.5** Keep historical coverage assertions attributed to their original baseline and require denominators and reviewed relationships for current coverage.

**Corresponding research note** Rosetta Stone semantics and mapping evidence. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Resolve one external requirement to exact AI SAFE2 clauses, engineering checks and evidence, then reverse the query. A missing or ambiguous external ID must produce an explicit unresolved result.


<a id="c52"></a>

### C52 Agent-consumable requirement and repair contracts

**Recommendation** Add explicit P2/P5 machine-interface child requirements.

**Source** Wave 02 retrieval interfaces; Wave 04 diagnosis; recovery files.

**Why and trade-off** Discoverability without precise contracts leaves agents guessing which version and evidence apply. Extend existing CLI/manifest ownership. A new interface must preserve schema compatibility and avoid granting decision authority.

**Draft requirements**

- **C52.1** Return canonical IDs, source revision, applicability, parent inheritance and evidence status in machine queries.
- **C52.2** Link each requirement to a test or declared verification gap and a supported repair or recovery path.
- **C52.3** Prevent ambiguous aliases and inferred crosswalk chains from producing authoritative compliance answers.
- **C52.4** Bind output to the assessed system and retain explicit unknown, partial, stale and unsupported states.

**Corresponding research note** Machine-readable governance for building and repair. Its question is whether the proposed requirement addresses the specific failure mechanism better than the existing parent alone. Preserve source facts, interpretations, counterevidence, deployment prerequisites and test limits.

**Validation and contrary-evidence test** Run a synthetic agent workflow that queries a requirement, applies a bounded fix and rechecks the failing test. Test stale editions, ambiguous aliases and a missing enforcement implementation.


## Pass 2 - Adversarial challenge to the expanded plan

| Challenge | Finding and resulting correction |
| --- | --- |
| Is runtime enforcement dominating the design? | Yes in the earlier priority framing. C33 and C37 add explicit design and success contracts. A valid execution can still follow an invalid specification. |
| Are we counting documentation as deployed protection? | Require separate specification, implementation, enforcement and validation status per claim. C36 and C38 expose missing observations and failures. |
| Does the plan favor CSI implementation availability? | The source JEV methodology weighted shipping CSI code heavily. Comparative conformance must allow alternative implementations that satisfy the same requirement. Record implementation availability separately from requirement quality. |
| Does absorbing proposals hide their substance? | C33-C38 become standalone candidates. C39-C52 enumerate child requirements and paired research. Every retained absorption needs a parent rewrite and a test demonstrating its fit. |
| Does evidence independence establish truth? | No general truth guarantee is established. C36 verifies a defined effect. C48 adds competence, conflict and contaminated-grader checks. |
| Does approval establish meaningful human authority? | C24 and C41/C46 require comprehension, justified reliance, accessibility and participation evidence. Numerical human-state proxies need validation before use as gates. |
| Can a compliant or secure system still cause harm? | C41 and C42 address validity, fairness, suitability and alternatives. Sector profiles preserve clinical, financial and physical consequence requirements. |
| Can the new controls create harm? | C35 treats key collisions and unknown settlement. C43 examines correlated fallback. C44 constrains emergency bypass. Verification burden and false refusal must be measured alongside prevented effects. |
| Does being mapped to many standards establish breadth? | The recovered files have multiple levels of detail. C51 requires atomic relationships and exposed gaps. Existing labels alone supply no superiority result. |
| Are old source claims being treated as current facts? | Register exact release/source dates and supersession. Historical screenshots, percentages and names remain attributed. Current claims require reviewed owners and current tests. |
| Can a new adversarial benchmark unfairly favor AI SAFE2? | Freeze the common scenario and denominators before comparing systems, publish failure cases and scope, permit alternative enforcement, and have an independent runner reproduce results. |
| Can mitigation degrade defensive utility? | Record legitimate completion, false blocks, outage handling, time to diagnose and recovery. Safe degraded operation needs explicit effect limits and authority. |

## Pass 3 - Reconsideration of deferred and unpromoted material

| Material revisited | Revised disposition, reason and reopening evidence |
| --- | --- |
| Design-time coordination as generic CP.4 guidance | Promote to C33 because deployment admission and graph validity differ from runtime authorization. Preserve original CP.11 proposal wording as history and allocate the canonical ID after the full catalog review. |
| Environment binding under general isolation | Promote C34. A destructive action needs verified target-environment identity even when the process itself is isolated. |
| Idempotency under generic recovery | Promote C35. Give key scope, atomic admission, ledger and unknown results explicit requirements. Reject a universal exactly-once guarantee where the destination cannot support it. |
| Verified completion under independent evidence | Promote C36 and retain C04. Evidence custody and verification of a particular external result are distinct obligations. |
| Success criteria under evaluation cadence | Promote C37. Evaluation must know the declared objective and protected constraints. Qualitative tasks retain a declared human rubric. |
| Failure diagnosis as a tooling feature only | Promote C38 and its bounded research comparison. A cause remains unverified until the evidence supports it. |
| Memory outcome annotation omitted in generic provenance | Promote explicit C39 clauses. A corrected memory must remain corrected through derived-state retrieval and restore. |
| Computer-use coverage absorbed into browser profile | Deepen C40 with native application and browser-specific child treatments. Profile publication can precede a reference runtime if its implementation status is explicit. |
| Fairness, participation and governance alternatives lightly mentioned | Promote C41, C42, C46 with applicable tests. These protect people whose harms arise under legitimate authority. |
| Portfolio concentration, emergencies and environmental impacts left as broad governance ideas | Promote C43, C44 and C47 with applicability-based requirements and measurement limits. |
| Additional standards, jurisdictions and sectors | Admit all source-backed discovery records into the source inventory, including CoSAI, AISVS, COSAiS and SPVS as distinct entries. No arbitrary framework limit. Clause mapping requires the actual edition and accessible controlling requirements. |
| Source-rights observations and competing obligations | Deepen C45. Observation, rights decision and reuse enforcement remain distinct records. Specialist applicability review resolves a particular conflict. |
| Human-state telemetry and universal psychological cutoffs | Retain explicit research and optional evaluated signals. The supplied materials do not establish validity for a universal runtime gate. Reopen on representative validation, privacy review, false-positive analysis and measured benefit. |
| EFA/FlowSignal wholesale adoption | Adopt supported properties and independently test the named implementation. Mandatory use of a single architecture requires a demonstrated unmet objective that equivalent implementations cannot satisfy. |
| First/only/best or legally definitive claims | Comparative findings need matched tasks, independent reproduction and source-pinned claims. Publish the actual comparative result and limits. An accessible paper alone establishes no measured lead. |
| Forecasts | Retain six-month scenarios with falsifiers. Document historical events and corrections as historical records with explicit confidence and remaining verification gaps. |

## Rosetta Stone expansion and machine checks

Preserve all recovered source identities and reconcile the seven crosswalk families with the 32-row register. Add source records from the full Wave 02 discovery inventory, with status for exact edition, access, licensing, scope and mapping unit. Compare public guidance, standards, regulations, threat taxonomies and scoring methods according to their different functions. Register official updates separately. OWASP's agent control and agentic skills material show that neighboring programs also evolve, so the comparative inventory needs an owned refresh process. [OWASP expansion announcement](https://genai.owasp.org/2026/09/01/owasp-genai-security-project-unveils-2026-top-10-for-llm-applications-new-agent-control-standard-and-sponsors-as-community-tops-30000-members/) · [OWASP skills project](https://owasp.github.io/www-project-agentic-skills-top-10/)

Implement the following check classes against individual records. These are 16 proposed validation rules, with executable implementation pending.

| Check | Required behavior |
| --- | --- |
| RS01 Source identity | Publisher, title, edition, status and canonical locator exist. |
| RS02 Locator validity | Referenced external mapping unit exists in that edition, with access limits explicit. |
| RS03 Internal identity | AI SAFE2 canonical control and child clause exist; ambiguous aliases fail resolution. |
| RS04 Relationship | State direction, full/partial/supporting/contradictory relationship, mechanism and rationale. |
| RS05 Applicability | Role, jurisdiction, system class and exclusions are recorded. |
| RS06 Direct grounding | A relationship inferred through another crosswalk cannot become an approved direct mapping. |
| RS07 Evidence scope | Implementation, enforcement and effectiveness claims link to evidence with exact revision and boundary. |
| RS08 Unknowns | Missing, stale, disputed and unassessed mappings remain queryable. |
| RS09 Coverage arithmetic | Numerator, denominator, excluded units and review status match the owning source inventory. |
| RS10 Reverse parity | External-to-internal and internal-to-external queries resolve the same relationship IDs. |
| RS11 Freshness | Source and control changes invalidate affected relationships for review. |
| RS12 Claim integrity | Historical coverage claims and third-party assertions cannot silently become current validation. |
| RS13 Evidence reuse | Shared evidence is accepted only when scope, role, time and obligation permit it. |
| RS14 Conflict handling | Inconsistent obligations or reviewer findings have an accountable disposition. |
| RS15 Distribution parity | Markdown, dashboard, CLI, skill and packaged data match canonical records. |
| RS16 Human/agent utility | Queries return requirement, applicability, test, evidence gap and supported repair path. |

## MCP child requirements made explicit

The 19 existing profile IDs remain the baseline for the mapping decision. The following twelve review clauses must be compared against their owning text. Where already normative, preserve the wording and add the missing test. Where coverage is incomplete, add or strengthen the child requirement. New profile IDs follow an objective-gap decision.

| Review clause | Existing control owner | Required nuance and negative case |
| --- | --- | --- |
| MCP-R01 | MCP-7, MCP-19 | Discovery and fallback cannot reduce identity or resource checks. Test missing discovery and unauthorized fallback. |
| MCP-R02 | MCP-19 | Bind inbound principal, intended resource and delegated purpose. Reject a valid token for the wrong resource. |
| MCP-R03 | MCP-4, MCP-7 | Trust must precede startup, install hooks and credential access where the client can enforce it. Test pre-trust effects. |
| MCP-R04 | MCP-11, MCP-18 | Catalog, schema and effective-permission changes invalidate affected approvals. Test a signed change that expands authority. |
| MCP-R05 | MCP-2, MCP-6 | Returned content and generated parameters cannot widen grants. Exercise each enabled input modality and destination validator. |
| MCP-R06 | MCP-8, MCP-10 | Aggregate concurrent work and outstanding commitments under the inherited task ceiling. Test individually permitted child requests that exceed the whole budget. |
| MCP-R07 | MCP-12, MCP-16 | State handles retain principal, tenant, scope, expiry and correction lineage. Test transfer and restored stale state. |
| MCP-R08 | MCP-13, MCP-10 | Revocation reaches cached grants, descendants and queued work. Record unreachable resources and isolate their effects. |
| MCP-R09 | MCP-17, MCP-5 | Retries preserve bound action identity and verified outcome. Test timeout after an external commit. |
| MCP-R10 | MCP-19, MCP-6 | Revalidate resolved destination and environment at use. Test redirect, account and resource substitution. |
| MCP-R11 | MCP-5 and P2 | Separate invocation, acceptance and observed postcondition in the evidence. Test false tool success. |
| MCP-R12 | MCP-9, MCP-19 | Tool, tenant and purpose boundaries survive service credential use. Test fallback to shared operator authority. |

## Research register and completion evidence

Each C33-C52 section above specifies a separate research-note question, its source lineage, competing interpretation, and a validation target. The register below makes the 20 new note proposals discoverable. The 32 earlier decision records retain their own note or revision obligations. Where a new question shares a prior note, add an independently named section and record why consolidation preserves the question. Never count an unchanged backlink as completed research.


| Research review ID | Question | Decision owners |
| --- | --- | --- |
| RN-C33 | Coordination before execution | C33; linked control/profile owner and validation reviewer |
| RN-C34 | Environment identity and destructive actions | C34; linked control/profile owner and validation reviewer |
| RN-C35 | Idempotency, ambiguity and settlement | C35; linked control/profile owner and validation reviewer |
| RN-C36 | Completion versus independently verified effect | C36; linked control/profile owner and validation reviewer |
| RN-C37 | Success criteria and useful work | C37; linked control/profile owner and validation reviewer |
| RN-C38 | Failure attribution and repair evidence | C38; linked control/profile owner and validation reviewer |
| RN-C39 | Memory validity and correction propagation | C39; linked control/profile owner and validation reviewer |
| RN-C40 | Computer-use authority and UI state | C40; linked control/profile owner and validation reviewer |
| RN-C41 | Fairness and valid decisions under authorized execution | C41; linked control/profile owner and validation reviewer |
| RN-C42 | AI necessity, alternatives and acceptable uncertainty | C42; linked control/profile owner and validation reviewer |
| RN-C43 | Concentration and common-mode containment | C43; linked control/profile owner and validation reviewer |
| RN-C44 | Emergency authority and exception persistence | C44; linked control/profile owner and validation reviewer |
| RN-C45 | Source rights through evidence retention and remedy | C45; linked control/profile owner and validation reviewer |
| RN-C46 | Affected-party participation and practical redress | C46; linked control/profile owner and validation reviewer |
| RN-C47 | Resource impacts beyond financial spend | C47; linked control/profile owner and validation reviewer |
| RN-C48 | Who validates the verifier | C48; linked control/profile owner and validation reviewer |
| RN-C49 | Observed actor tradecraft and deployment relevance | C49; linked control/profile owner and validation reviewer |
| RN-C50 | Adoption, operator burden and useful defense | C50; linked control/profile owner and validation reviewer |
| RN-C51 | Rosetta Stone semantics and mapping evidence | C51; linked control/profile owner and validation reviewer |
| RN-C52 | Machine-readable governance for building and repair | C52; linked control/profile owner and validation reviewer |

Every note needs a dated source/claim register, events versus disclosures, laboratory versus operational evidence, limits and contrary findings, exact old/new requirement comparison, why standalone or absorbed, applicable actors/surfaces, proposed enforcement, regression cases, recovery, and supported claims. Primary-source status verification remains necessary for external legal duties and historical incident causes. This review supplies a comprehensive framework expansion and its reasoning. Executed validation determines implementation and effectiveness claims.

The [33-family recovery audit](data/framework-mapping-recovery-review-2026-11-19.csv) preserves the recorded counts and historical assertions with an explicit unassessed coverage status.

## Supplied source fingerprints

- `source-extracts.md` SHA-256 `fcdcd451e025401ae5f86171336fbb84cd6144ae99226a52537ee922fed43742`.
- `aism-clause-crosswalk.csv` SHA-256 `f93b415d9954015d66546efe9b5092a1c1de5ea0969d06e6beb5d3ab3c1a9a72`.
- `control-framework-links.csv` SHA-256 `e70d02af343dda8c795ca3811d9ccdac6701641a8f287a20436136b79b5c2b10`.
- `framework-register.csv` SHA-256 `c61568388b86a2c123eabaa611c1686fe699e7acd846c293d94baf4f02cfef41`.

[Shared documentation](README.md) · [Open issue resolution](FRAMEWORK-UPDATE-ISSUES.md)
