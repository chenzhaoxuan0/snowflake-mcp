# snowflake-mcp

A Snowflake data warehouse MCP server powered by [Dedalus](https://dedaluslabs.ai).

## Tools

| Tool | Description | Read/Write |
|------|-------------|-----------|
| `list_databases` | List Snowflake databases | Read |
| `list_schemas` | List schemas in a database | Read |
| `list_tables` | List tables in a schema | Read |
| `describe_table` | Describe columns of a table | Read |
| `run_query` | Run SQL query (SELECT-only by default) | Read/Write |
| `list_warehouses` | List Snowflake warehouses | Read |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SNOWFLAKE_ACCOUNT` | Yes | Account identifier (e.g., `xy12345.us-east-1`) |
| `SNOWFLAKE_TOKEN` | Yes | Programmatic Access Token or OAuth token |
| `SNOWFLAKE_TOKEN_TYPE` | No | Token type header (default: `PROGRAMMATIC_ACCESS_TOKEN`) |
| `SNOWFLAKE_WAREHOUSE` | No | Default warehouse |
| `SNOWFLAKE_DATABASE` | No | Default database context |
| `SNOWFLAKE_SCHEMA` | No | Default schema context |
| `DEDALUS_API_KEY` | Yes | Dedalus platform API key |
| `DEDALUS_API_URL` | No | Dedalus API base URL |
| `DEDALUS_AS_URL` | No | Dedalus auth server URL (default: `https://as.dedaluslabs.ai`) |

## Auth Architecture

**Type 3 DAuth (SQL API REST)**. This server uses the Snowflake SQL API (`POST /api/v2/statements`) with a Bearer token managed through DAuth dispatch. All requests go through `ctx.dispatch()` — tool code never reads the token.

Users must create a Programmatic Access Token in Snowflake:

```sql
CREATE PROGRAMMATIC ACCESS TOKEN my_mcp_token
  ROLE = SYSADMIN
  EXPIRY = 90 DAYS;
```

See `docs/auth-architecture.md` for details.

## `run_query` Safety

- **Default**: Only SELECT, SHOW, DESCRIBE, WITH, EXPLAIN, and USE statements are allowed
- **`allow_writes=True`**: Enables INSERT, UPDATE, DELETE, CREATE, DROP, etc. A warning is included in the result
- Multi-statement SQL with writes is rejected unless `allow_writes=True`
- Results are truncated at `max_rows` (default 100, max 1000)
- Identifiers are quoted to prevent SQL injection

## Quick Start

```bash
uv sync
cp .env.example .env
# Edit .env with your Snowflake account and token
uv run python src/main.py
```

## Testing

```bash
uv run pytest tests/test_tools.py tests/test_sql_safety.py tests/test_transport.py tests/test_security.py -v

# Live tests (requires Snowflake credentials)
uv run pytest tests/test_connection_live.py -v
```

## Examples

```python
# List databases
result = await client.call_tool("list_databases", {})

# List schemas in a database
result = await client.call_tool("list_schemas", {"database": "SNOWFLAKE_SAMPLE_DATA"})

# Describe a table
result = await client.call_tool("describe_table", {
    "table": "CUSTOMER",
    "database": "SNOWFLAKE_SAMPLE_DATA",
    "schema": "TPCH_SF1"
})

# Run a read-only query
result = await client.call_tool("run_query", {
    "sql": "SELECT COUNT(*) AS cnt FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER"
})
```

## Source Decision

**Build native (Python REST via SQL API)**. No official Snowflake MCP exists. The SQL API REST with DAuth-managed PAT token is the only approach that achieves full Type 3 DAuth compliance. See `docs/source-selection.md` for details.

## License

MIT
