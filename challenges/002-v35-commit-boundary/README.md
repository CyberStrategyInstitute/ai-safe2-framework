# Challenge 002 | Authority, effects and useful work

This prospective protocol addresses the live-study denominator gap from issue #308. It leaves the frozen Challenge 001 artifacts intact. No confirmatory trial or independent reproduction has been performed.

The [preregistration candidate](preregistration.json) selects episode as the common primary exposure unit and retains raw unauthorized effects, opportunity counts, attempted/blocked actions, legitimate completion, false blocks and unknowns separately. Treatments can change the number of opportunities, so conditional rates require separate interpretation. Zero denominators remain undefined.

The local authority fixture in `safe2.authority_fixture` and `tests/test_framework_v35.py` exercises changed approvals, stale resource/environment state, aggregate budgets, duplicate effects, revocation and PAUSE/ESCALATE outcomes. The synthetic resource and ledger share one SQLite transaction. This boundary cannot establish atomicity for remote APIs or independent verifier assurance. Protect the fixture database and approval key outside acting-agent access in any adapted deployment.

Before live confirmatory work, finalize and freeze the task corpus, assignment, episode count, exposure window, opportunity definition and analysis plan. Retain unknown outcomes and adverse utility findings. Use an independent runner and publish exactly which effect boundary was exercised.

[Challenge Lab](../README.md) | [Framework home](../../README.md) | [Control contracts](../../docs/CONTROLS-V3.5.md)
