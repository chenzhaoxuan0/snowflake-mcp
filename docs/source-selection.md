# Source Selection: Snowflake MCP

**Decision:** Build native using Snowflake SQL API REST with DAuth-managed token.

## Evaluation

### Official Snowflake MCP

Snowflake-Labs does not ship a general-purpose Snowflake MCP server. Cortex has AI features but no MCP protocol implementation.

### Community: `isaacwasserman/mcp-snowflake-server`

- Uses `snowflake-connector-python` for direct DB connections
- Python, but minimal SQL validation
- No DAuth integration
- Not adaptable to Type 3 DAuth dispatch pattern

### Snowflake SQL API (REST)

- `POST /api/v2/statements` for SQL execution
- Auth requires `Bearer` token (OAuth, key-pair JWT, or Programmatic Access Token)
- Standard REST API, works naturally with DAuth `ctx.dispatch()`
- No SDK dependency needed

### `snowflake-connector-python` SDK

- Accepts user/password or private-key credentials directly
- Not compatible with DAuth dispatch pattern
- SDK manages its own wire protocol

## Decision: SQL API REST + DAuth (Type 3 Compliant)

Use Snowflake SQL API REST with Programmatic Access Token (PAT) or OAuth token, managed through DAuth `Connection` + `SecretKeys` + `ctx.dispatch()`.

This is the only approach that achieves full Type 3 DAuth compliance:

1. Token is stored as DAuth secret (`SNOWFLAKE_TOKEN`)
2. All SQL requests routed through `ctx.dispatch()` — tool code never sees the token
3. Standard `Connection` object with `Bearer {api_key}` auth header format
4. No SDK dependency needed

### Credential Change

- Old: `SNOWFLAKE_PASSWORD` / `SNOWFLAKE_PRIVATE_KEY` (SDK direct)
- New: `SNOWFLAKE_TOKEN` (PAT or OAuth) via DAuth
- Users need to create a Programmatic Access Token in Snowflake: `CREATE PROGRAMMATIC ACCESS TOKEN ...`
