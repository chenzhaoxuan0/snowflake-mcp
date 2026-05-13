# Auth Architecture: Snowflake MCP

**ADR-001: SQL API REST + DAuth Token (Type 3 Compliant)**

## Status

Accepted — full Type 3 DAuth compliance.

## Context

Standard Type 3 DAuth servers use `Connection` + `SecretKeys` + `ctx.dispatch()` to route authenticated HTTP requests through the DAuth enclave. Tool code never reads credentials.

Snowflake SQL API (`POST /api/v2/statements`) requires a `Bearer` token. Supported token types:

1. **Programmatic Access Token (PAT)** — created via `CREATE PROGRAMMATIC ACCESS TOKEN` in Snowflake
2. **OAuth 2.0 access token** — from a configured Security Integration
3. **Key-pair JWT** — signed with a private key (requires key material exposure)

## Decision

Use SQL API REST with PAT or OAuth token, managed through DAuth dispatch. The token is stored as `SNOWFLAKE_TOKEN` env var, registered as a DAuth secret, and injected into requests via the standard `Connection` auth flow.

```python
snowflake_conn = Connection(
    name="snowflake",
    secrets=SecretKeys(token="SNOWFLAKE_TOKEN"),
    base_url="https://<account>.snowflakecomputing.com",
    auth_header_format="Bearer {api_key}",
)
```

Every tool calls `ctx.dispatch()` which routes through DAuth. Tool code never reads `SNOWFLAKE_TOKEN`.

Additional header `X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN` is attached in the dispatch helper.

## Consequences

- **Full Type 3 DAuth**: Token managed by DAuth enclave, never exposed to tool code
- **No SDK dependency**: Pure REST via `ctx.dispatch()`
- **Credential contract**: Users must provide a PAT or OAuth token (not password/private key)
- **Security mitigations**:
  - Token never in tool code, logs, or error messages
  - `run_query` defaults to SELECT-only with `is_read_only_sql()` enforcement
  - Max row truncation prevents large result leaks
  - Identifier quoting prevents SQL injection

## Credential Mode

| Variable | Required | Purpose |
|----------|----------|---------|
| `SNOWFLAKE_ACCOUNT` | Yes | Account identifier (e.g., `xy12345.us-east-1`) |
| `SNOWFLAKE_TOKEN` | Yes | PAT or OAuth token |
| `SNOWFLAKE_TOKEN_TYPE` | No | Token type header (default: `PROGRAMMATIC_ACCESS_TOKEN`) |
| `SNOWFLAKE_WAREHOUSE` | No | Default warehouse for queries |
| `SNOWFLAKE_DATABASE` | No | Default database context |
| `SNOWFLAKE_SCHEMA` | No | Default schema context |

## Previous Approach (Superseded)

v0.0.1 used `snowflake-connector-python` SDK with direct password/private-key auth. This violated Type 3 DAuth requirements. Replaced with SQL API REST + DAuth in v0.1.0.
