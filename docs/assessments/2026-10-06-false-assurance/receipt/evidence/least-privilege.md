# Least-privilege review (agent-performed, mechanical)

## .github/workflows/ci.yml
```
permissions:
  contents: read

```
## .github/workflows/opa.yml
```
permissions:
  contents: read

```
- ci.yml: no permissions block on main (repository default token scope); now `contents: read` at workflow level. No job writes or calls the API.
- opa.yml: `contents: read`, checkout with `persist-credentials: false`.
- No new secrets, tokens or write scopes introduced. Test servers bind 127.0.0.1 only; throwaway tokens are assembled at run time.
- Guardian/OPA changes only narrow authority: undeclared tier treated as ACT-4, explicit deny gates allow, most-restrictive persistence scope wins.
