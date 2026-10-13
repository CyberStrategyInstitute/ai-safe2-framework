# MCP Python SDK v1 to v2 migration contract

Reviewed: 2026-10-13. Target for a future migration: SDK v2.3.0.
Current supported knowledge-server range: `mcp>=1.12,<2`.
Status: migration planning only; v2 runtime behavior is NOT TESTED here.

## Immediate release boundary

PR #408 widens only the knowledge-server requirement to `<3`. Its hosted
install/start/auth job fails while importing the removed `streamablehttp_client`.
The application also imports `mcp.server.fastmcp.FastMCP`. Changing one import
does not qualify the other server, transport, or authorization contracts.
Keep the v1 bound for NEXUS 0.6 qualification and disable Dependabot major
updates for this dependency while retaining minor/patch updates.

Python SDK version and MCP protocol specification date are different axes.
An SDK upgrade does not establish implementation of the 2026-07-28 profile.
`server/discover` remains optional in the framework binding. A session handle
is not a principal or an authorization grant.

## Component ownership and existing contracts

| Component | Current implementation | Migration consequence |
| --- | --- | --- |
| Knowledge server | `src/mcp_server/app.py`, `auth.py`, `context.py`; direct SDK consumer | Must migrate server/client types and requalify stdio, HTTP, tier propagation, authentication, resources, and prompts. |
| NEXUS | `NEXUS/adapters/mcp/adapter.py`; explicit fail-closed skeleton, not production-ready | Do not turn migration into adapter implementation. Test that every unimplemented boundary still raises; any future binding needs principal/capability, header/body, provenance, and retry controls. Guardian, AgBOM, OPA, and ACT behavior remain separately qualified SDK behavior. |
| Gateway | `gateway/main.py`, `provider_adapters.py`; north-south HTTP gateway, no direct MCP SDK import in the reviewed paths | No mechanical SDK rename required. Requalify any integrated MCP path for approval binding, cancellation, accounting, and per-call authorization. North-south results do not prove agent-to-tool enforcement. |
| MCP Toolkit | `aisafe2_mcp_tools/wrap/{proxy,wrapper,scanner,policy,audit}.py`; protocol proxy, not an SDK server | Preserve direct request checks and returned-content scanning. Catalog filtering alone is not tool-call authorization. Requalify wire envelopes, header/body handling, schema pinning, retries, and streaming with real v2 fixtures. |
| Tests and packaging | `tests/test_mcp_dependency_boundary.py`, `skills/mcp/tests/test_transport_e2e.py`, `.github/workflows/ci.yml` | The guard must reject dependency-only widening. A future migration replaces it deliberately after compatibility evidence, not by skipping transport tests or catching import errors. |

## Required implementation and regression matrix

Every row is a future acceptance requirement, not an implemented feature or a
passing test. K = knowledge server; N = NEXUS; G = Gateway; T = MCP Toolkit.

| ID / upstream change | Required code decision and affected components | Required regression evidence |
| --- | --- | --- |
| V2-01: `FastMCP` becomes `MCPServer` | K: use `mcp.server.mcpserver.MCPServer`; audit decorators, tools, resource templates, prompts, and injected Context. N/G/T: no direct rename in reviewed paths. | Fresh wheel imports and starts; expected tool/resource/prompt names and schemas remain available over both transports. |
| V2-02: removed `streamablehttp_client`; new client yields two streams | K/tests: use `streamable_http_client`, unpack `(read, write)`, configure auth/headers/timeouts on `httpx2.AsyncClient`. N/G/T: review any added SDK client separately. | Actual handshake, list, call, teardown, invalid auth, and lifecycle failure tests; no hidden import fallback. |
| V2-03: `httpx2` and dependency changes | K: audit SDK-facing client, auth, mock, and exception types; keep `httpx` for unrelated code if needed. G/T: existing raw HTTP clients need not be renamed. | Clean resolves on supported Python versions; HTTP-error classification, TLS trust-store behavior, SSE and auth fixtures; dependency audit. |
| V2-04: transport settings move; shared server lifespan | K: pass transport options to app/run methods; preserve outer Starlette session-manager lifespan. N/G/T: never put principal/tier/approval state in shared lifespan state. | Start/stop and restart; parallel free/pro clients; tier reset, request isolation, hostile Host/Origin, and no authenticated HTTP 500. |
| V2-05: invalid `x-mcp-header` rejected at registration | K: audit annotations only where headers are deliberately exposed; plain string/int/bool and valid distinct header names; explicit schema for optional headers. N: future header/body binding; T: inspect forwarded header annotations; G: retain its own validation. | Reject invalid types, duplicate case-insensitive names and malformed names before serving; valid registrations remain callable. |
| V2-06: empty `_meta` / `params` omitted on legacy connections | K: optional context metadata must tolerate `None`. N/T: parsers must distinguish absent, null, object, and malformed parameters; G: integrated path must preserve authority semantics. | Ping/list with absent params; missing/empty/null metadata; reject malformed tool arguments without bypassing checks; preserve approved argument identity. |
| V2-07: absent `experimental`; initialize versus discover | K/client tests: select and record negotiated mode explicitly; tolerate absent capabilities. N/T: keep protocol version distinct from principal. G: do not promote probe errors to authorization. | Legacy initialize and current discovery fixtures; server without discover works through the approved compatibility path; absent experimental is accepted. |
| V2-08: per-tool schema lookup replaces implicit `tools/list` | K: validate at registration and at the callable tool boundary. N: future capability checks must apply on every call. T: retain explicit denied-name enforcement and provenance checks; G: do not rely on catalog visibility for approval. | A removed/hidden tool invoked by name is still denied at the enforcing boundary; schema change cannot alter an already approved call; no dependence on an implicit list request. |
| V2-09: interactive OAuth excluded from request timeout | K: if OAuth is added, set independent callback/login deadlines and cancellation; existing bearer middleware is not OAuth. N/G/T: bind auth to intended resource and principal, never session ID. | Slow login succeeds inside its explicit budget; abandoned login terminates; cancellation cleans up; wrong audience, expired/revoked credentials and cross-principal reuse fail. |
| V2-10: high-level call retries once after HeaderMismatch | K/client: choose explicit retry policy; N/G/T: recheck authorization, argument binding, revocation, and provenance on every attempt; use stable operation identity for consequential actions. | At most the documented retry; no duplicate side effect or charge; changed args, revoked approval, or catalog mismatch cannot pass on retry. Test the high-level Client, not only ClientSession. |
| V2-11: explicit null structured content is schema-validated | K: review every tool output schema; T: sanitize both text and structured outputs; N/G: preserve the observed result without inventing success. | Missing and explicit-null outputs differ appropriately; invalid output fails; malicious structured content is withheld; existing typed outputs still validate. |
| V2-12: timeout values and errors change | K: float seconds replace timedelta where required; audit MCPError versus HTTP exception handling. N/G/T: retry/error classification cannot convert unavailable evidence into allow. | Timeout, cancellation, unavailable server and non-2xx responses preserve failure meaning; configured fail-closed paths hold; no unbounded retry. |
| V2-13: pagination, typed fields and removed low-level APIs | K/tests: audit snake_case field access, params-based cursors, capabilities and dispatcher use; N/T: preserve wire aliases and unknown fields intentionally; G: no direct dependency. | Multi-page listings; serialized output/schema compatibility; null-id error correlation; resource/prompt Context works; no removed private API use. |
| V2-14: SSE event size, subscriptions and back channels | K: retain a bounded event size; declare subscription capabilities intentionally; qualify stateful/stateless and JSON modes separately. N/G/T: bound streaming resources and document unsupported server-initiated calls. | Oversized event rejected; streaming disconnect/reconnect; subscription disabled behavior; unsupported back-channel calls fail explicitly; no silent data loss. |
| V2-15: telemetry and progress callback behavior | K: record errors without relying on progress callback exceptions to cancel a call. N/G/T: distinguish optional discovery probe failure from tool execution failure. | JSON-RPC failures remain visible; raising progress callback does not fake cancellation or success; logs redact tokens and user payloads. |
| V2-16: stdio process, output and platform changes | K/tests: qualify subprocess shutdown and stderr drainage; T: preserve wrapper process cleanup and protocol channel integrity; N/G: indirect integration only. | Windows and Linux process start/stop; stdout remains protocol-only; bounded stderr; cancellation, child cleanup and no leaked test servers. |

## Migration sequence and exit gate

1. Use a separate branch and isolated v2 environment. Pin the candidate SDK and
   capture the full dependency resolution; no mixed v1/v2 fallback.
2. Migrate K APIs and fixtures first. Run its complete suite, including real
   transports, auth/rate limits, resources, prompts, sanitization and tiers.
3. Run NEXUS, Gateway and Toolkit integration scenarios with target-side
   observations where an enforcement claim is made. Preserve the adapter's
   NOT IMPLEMENTED / NOT TESTED boundary.
4. Store version-bound evidence for V2-01 through V2-16. Name unimplemented
   surfaces and supported modes explicitly; do not treat a planned test as PASS.
5. Require deterministic checks, installed artifacts, dependency audit,
   attributed advisory review, and owner approval for the exact candidate.
6. Only then replace `<2` and the major-update exclusion in the same migration
   PR. Roll back to the qualified v1 range and artifact if acceptance fails.

## Sources and limitations

- [Official v1-to-v2 guide](https://py.sdk.modelcontextprotocol.io/migration/).
- [SDK v2.3.0 release and exact source tag](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0).
- [Failing dependency candidate #408](https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/408).
- [NEXUS 0.6 release candidate #399](https://github.com/CyberStrategyInstitute/ai-safe2-framework/pull/399).

Upstream descriptions identify changes; local static inspection identifies
applicability. Neither proves v2 runtime behavior. This matrix covers identified
consumer paths and release-note risks, not every upstream API or deployment.
