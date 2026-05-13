# Source Selection: Snowflake MCP

**Decision:** Build native using `snowflake-connector-python` SDK.

## Evaluation

### Official Snowflake MCP

Snowflake-Labs does not ship a general-purpose Snowflake MCP server as of 2025-05. Cortex has AI features but no MCP protocol implementation.

### Community: `isaacwasserman/mcp-snowflake-server`

- Uses `snowflake-connector-python` for direct DB connections
- SQL validation is minimal
- No DAuth integration
- TypeScript-based tool definitions
- Not adaptable to our Python + DAuth framework

### Snowflake SQL API (REST)

- `POST /api/v2/statements` for SQL execution
- Auth requires `Bearer` token (OAuth, key-pair JWT, or programmatic access token)
- Password-based credentials from Owner 3 cannot be used directly with SQL API
- Generating a JWT from a private key inside tool code would expose secrets, violating DAuth principles

## Decision: SDK Direct (ADR Exception)

`snowflake-connector-python` is the only viable option because:

1. Owner 3 provides password/private-key credentials, not OAuth tokens
2. SQL API requires bearer tokens that cannot be derived from password credentials without exposing secrets
3. The connector library handles auth, session management, and result formatting natively

This is an explicit exception to standard Type 3 DAuth dispatch. See `auth-architecture.md` for details.
