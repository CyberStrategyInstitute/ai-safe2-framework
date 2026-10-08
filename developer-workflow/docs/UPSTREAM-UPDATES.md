# Upstream Update Policy

Upstream releases are monitored, not executed directly from a moving branch.

```text
release detected
  -> isolated update pull request
  -> immutable version, SHA, or digest
  -> compatibility and security fixtures
  -> AI SAFE2 evidence comparison
  -> owner approval
  -> promotion or rollback
```

Rules:

- never depend on an upstream `main` branch at runtime;
- use one update authority, such as Dependabot or Renovate;
- apply security updates promptly through an isolated pull request;
- group routine patch updates weekly;
- use a 7-day cooldown for minor changes and 14 days for major changes;
- pin GitHub Actions to immutable commit SHAs;
- retain the previous known-good version;
- do not allow an adapter to approve its own upgrade;
- rerun acceptance and adversarial fixtures before promotion.

`upstreams.lock.json` is an inventory and policy input. It does not download or
execute an upstream project.

