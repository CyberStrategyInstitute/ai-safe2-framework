<!-- stack: AISM Decision Support -->
<!-- description: Executable assessment demonstrating evidence-aware AISM scoring and a human Decision Card. -->

# AISM Decision Card Example

This example turns a bounded agent environment assessment into two products:

- canonical JSON for agents and governance systems;
- a compact Markdown Decision Card for accountable humans.

It demonstrates facts, assumptions, conflicts, unknowns, history, alternatives,
an attributed outcome estimate, and a recommendation. The example is decision
support; it is not a claim of organizational maturity or full AI SAFE²
conformance.

## Run

```bash
cd examples/aism-decision-card
safe2 aism score assessment.json --format markdown --output decision-card.md
safe2 aism score assessment.json --format json --output decision.json
safe2 aism score assessment.json --format html --output decision-card.html
safe2 example verify aism-decision-card
python smoke_test.py
```

## Expected decision

The example returns `HOLD` because it intentionally contains a critical
conflict between a declared fail-closed policy and observed runtime behavior.
Resolving the conflict in the source assessment changes the recommendation;
the expected result is therefore testable rather than decorative.
