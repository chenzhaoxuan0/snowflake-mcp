# Auth Architecture: Snowflake MCP

**ADR-001: SDK Direct Connection (Exception)**

## Status

Accepted — explicit exception to standard Type 3 DAuth dispatch.

## Context

Standard Type 3 DAuth servers use `Connection` + `SecretKeys` + `ctx.dispatch()` to route authenticated HTTP requests through the DAuth enclave. Tool code never reads credentials.

Snowflake has two access paths:

1. **SQL API (REST)**: Requires `Bearer` token. Token types: OAuth, key-pair JWT, programmatic access token. Password credentials cannot produce a valid bearer token without secret exposure.
2. **`snowflake-connector-python` SDK**: Accepts user/password or private-key credentials directly. Manages session, authentication, and wire protocol internally.

Owner 3 provides: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD` (or `SNOWFLAKE_PRIVATE_KEY`), `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`.

## Decision

Use `snowflake-connector-python` SDK with direct credential reads from environment variables. Credentials are read in a single centralized module (`transport.py`). Tool code calls transport methods and never accesses credentials.

## Consequences

- **No DAuth dispatch**: Connection management bypasses the DAuth enclave
- **Credential exposure**: Password is read by application code at runtime (not logged or returned in results)
- **Security mitigations**:
  - All credential reads centralized in `transport.py`
  - No secret values in error messages, logs, or tool results
  - `run_query` defaults to SELECT-only with `is_read_only_sql()` enforcement
  - Max row truncation prevents large result leaks
  - Identifier quoting prevents SQL injection

## Credential Mode

| Variable | Required | Purpose |
|----------|----------|---------|
| `SNOWFLAKE_ACCOUNT` | Yes | Account identifier (e.g., `xy12345.us-east-1`) |
| `SNOWFLAKE_USER` | Yes | Username |
| `SNOWFLAKE_PASSWORD` | Yes* | Password auth (mutually exclusive with PRIVATE_KEY) |
| `SNOWFLAKE_PRIVATE_KEY` | No* | Key-pair auth path |
| `SNOWFLAKE_WAREHOUSE` | No | Default warehouse for queries |
| `SNOWFLAKE_DATABASE` | No | Default database context |
| `SNOWFLAKE_SCHEMA` | No | Default schema context |

*One of PASSWORD or PRIVATE_KEY is required.

## Alternative Considered

SQL API with DAuth-managed OAuth token was preferred but rejected because:
- Owner 3 credential contract does not include OAuth tokens
- Generating JWTs from private keys would expose key material to tool code
- Requesting a credential contract change adds deployment complexity
