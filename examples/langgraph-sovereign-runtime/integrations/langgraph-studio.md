# LangGraph Studio Notes — AI SAFE² v3.0

## Local Deployment (Standard)

Wrap node functions before adding to the graph. Enforcement runs in-process.

```python
sovereign = SovereignStateGraph(act_tier=ACTTier.ACT3)
graph.add_node("researcher", sovereign.wrap_node("researcher", researcher_fn))
```

## LangGraph Studio (Local Dev Mode)

LangGraph Studio runs graphs locally via the LangGraph CLI. Sovereign wrappers
work identically — the node functions are still Python callables.

## LangGraph Cloud (If Requested)

Cloud streaming execution uses `graph.astream()`. Use `wrap_node_async()`:

```python
graph.add_node("researcher", sovereign.wrap_node_async("researcher", researcher_fn))
result = await compiled.ainvoke(state)
```

Enforcement is identical. The async wrapper runs the sync enforcement in a thread pool.

## Checkpointer Integration (S1.5)

LangGraph checkpointers persist state. Gate writes before they reach the checkpointer:

```python
# Before writing to SqliteSaver / PostgresSaver
clean_state = sovereign.protect_state_write(state_update, source_node="my_node")
```
