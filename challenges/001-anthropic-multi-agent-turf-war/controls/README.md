# Controls

Implementations are separated into:

- `conventional/`: isolation, Unix permissions, RBAC, quotas, and ordinary logging;
- `nexus/`: identity, VCC, Guardian, NOR, Memory Vaccine, and related protocol controls;
- `ai-safe2/`: treatment composition, ACT-tier requirements, HEAR, containment, monitoring, recovery, and control mappings.

This separation enables incremental-value and ablation testing.
