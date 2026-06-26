# CrewAI Flows Integration — AI SAFE² v3.0

## Flows vs Crews

CrewAI Flows (introduced in 0.70+) use event-driven routing rather than
sequential/hierarchical task execution. The sovereign enforcement model adapts:

### Standard Crew (Sequential/Hierarchical)
- `wrap_agent()` on each agent
- `protect_task_output()` after each task
- `wrap_crew()` for automatic task_callback injection

### CrewAI Flows
In Flows, `@listen` decorators chain methods. Gate outputs at each step:

```python
from crewai.flow.flow import Flow, listen, start
from enforcement import SovereignCrew, ACTTier

sovereign = SovereignCrew(act_tier=ACTTier.ACT3)

class SovereignResearchFlow(Flow):
    @start()
    def research(self):
        result = self.research_crew.kickoff()
        # Gate before state advances to next step
        return sovereign.protect_task_output(str(result), "research_step")

    @listen(research)
    def write(self, research_output):
        # research_output already scanned — safe to use
        result = self.writing_crew.kickoff(inputs={"research": research_output})
        return sovereign.protect_task_output(str(result), "write_step")
```

### Shared Engine in Flows

```python
# One engine for all crews within the Flow
from enforcement.ai_safe2_engine import AISAFE2Engine, ACTTier

shared_engine = AISAFE2Engine(act_tier=ACTTier.ACT3)
sovereign = SovereignCrew(engine=shared_engine)
# All steps share one compliance score and one audit chain
```
