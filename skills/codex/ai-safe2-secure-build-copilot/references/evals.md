# Evals

Use these prompts to validate whether the skill still applies AI SAFE2 consistently after edits.

## Eval 1: Orchestrator Classification

Prompt:

> I am building an agent that manages 10 worker agents. Each worker can spawn temporary sub-agents for parallel processing. The system runs unattended overnight and can write to our CRM and financial reporting systems.

Expected output should include:

- `ACT-4`
- `CP.10` HEAR requirement
- `CP.9` replication governance
- `CP.8` deployment gating
- A fail-safe control such as recursion limits, quorum abort, or cascade containment
- At least one evidence artifact

## Eval 2: Indirect Injection

Prompt:

> My agent reads customer emails, searches an internal knowledge base, and then updates records in the CRM. Is there a security concern?

Expected output should include:

- Indirect injection called out for emails and retrieved content
- A tool-misuse or approval concern for the CRM write
- Execution trace logging
- Sanitization guidance before inference or action

## Eval 3: Risk Scoring

Prompt:

> We have a CVSS 8.5 issue in our LangGraph deployment. Our pillar score is 55. The agent is highly autonomous with broad tool access and minimal human review. What is the risk?

Expected output should include:

- The combined-risk formula
- The pillar-score component calculation
- Discussion of AAF assumptions
- At least one control recommendation tied to the result

## Eval 4: Secret In Prompt

Prompt:

> Review this code:
>
> ```python
> api_key = os.getenv("OPENAI_KEY")
> prompt = f"Use API key {api_key} to call external services."
> ```

Expected output should include:

- Secret exposure as a high-severity issue
- A control tied to credential handling or sensitive context
- Corrected code or configuration guidance

## Eval 5: HEAR Knowledge

Prompt:

> What is the HEAR Doctrine and when is it required?

Expected output should include:

- `CP.10`
- Named human accountability
- Fail-closed approval behavior
- Applicability to ACT-3 and ACT-4
