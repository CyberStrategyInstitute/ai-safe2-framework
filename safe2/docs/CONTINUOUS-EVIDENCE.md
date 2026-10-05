# Continuous Local Evidence

`safe2 evidence watch` turns the one-shot agent-input change monitor into an
explicit local polling runner. It inventories tracked skills and harness
configuration, rescans changed skill packages, preserves an immutable report for
every run, and atomically advances a validated state file.

```bash
# Establish the first explicit baseline and report
safe2 evidence watch . \
  --state .safe2/watch-state.json \
  --evidence-dir .safe2/evidence/changes

# Continue until interrupted
safe2 evidence watch . \
  --state .safe2/watch-state.json \
  --evidence-dir .safe2/evidence/changes \
  --continuous --interval 60

# CI or scheduled bounded run
safe2 evidence watch . \
  --state .safe2/watch-state.json \
  --evidence-dir .safe2/evidence/changes \
  --continuous --max-runs 3 --interval 10 --strict
```

The first run normally returns `hold` because all tracked configuration is new.
An unchanged validated baseline returns `approve`; changed agent configuration
returns `hold`; a static skill gate can return `hold` or `reject`. `--strict`
preserves the report and then exits nonzero on either review state.

This is detection and evidence preservation, not interception or enforcement.
Polling can observe a file only after it reaches the declared filesystem root.
It cannot see text pasted only into an agent context, prevent installation, prove
authorship or intent, or guarantee that every harness uses the scanned copy. Use
a harness pre-install/pre-load hook for prevention and treat this runner as an
independent, local evidence layer. It exports no content or telemetry by default.
