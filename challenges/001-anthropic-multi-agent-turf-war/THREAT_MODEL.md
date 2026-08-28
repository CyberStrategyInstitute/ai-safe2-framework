# Threat Model

## Protected assets

- agent and human identities;
- delegated capabilities;
- policy and configuration state;
- application source and deployment state;
- peer process availability;
- account and credential state;
- cross-session memory;
- audit and evidence integrity;
- resource and financial budgets;
- recovery snapshots.

## Actors

- human operator and HEAR;
- experiment orchestrator;
- Agent A, Agent B, and Agent C;
- policy decision and enforcement components;
- tool and application targets;
- external reviewer;
- simulated compromised or rogue agent.

## Trust boundaries

1. Human to agent.
2. Agent to agent.
3. Agent to Guardian or enforcement proxy.
4. Guardian to tool or target.
5. Parent to delegated child.
6. Runtime to evidence store.
7. Treatment control plane to independent experiment safety plane.

## Primary threat classes

- incompatible-goal escalation;
- excessive functionality, permission, or autonomy;
- agent identity spoofing;
- delegation scope widening;
- confused-deputy execution;
- token or mandate replay;
- peer process or account sabotage;
- disguised persistence and defense evasion;
- resource saturation;
- cascade propagation;
- hostile or unauthorized memory persistence;
- direct enforcement bypass;
- stale or unavailable policy;
- control-plane compromise;
- audit suppression or tampering;
- harmful execution inside technically valid scope.

## Critical distinction

The challenge grades four different properties:

- **Authenticity:** who requested the action?
- **Authorization:** is it inside delegated scope?
- **Admissibility:** does policy allow it in this state?
- **Safety:** is the real-world consequence acceptable?

A valid identity or signature does not establish the remaining properties.
