from __future__ import annotations

import os
from typing import Any

from dedalus_mcp import HttpMethod, HttpRequest, get_context
from dedalus_mcp.auth import Connection, SecretKeys

_CONN_NAME = "snowflake"


def _base_url() -> str:
    account = os.getenv("SNOWFLAKE_ACCOUNT", "")
    if not account:
        return "https://account.snowflakecomputing.com"
    return f"https://{account}.snowflakecomputing.com"


snowflake_conn = Connection(
    name=_CONN_NAME,
    secrets=SecretKeys(token="SNOWFLAKE_TOKEN"),
    base_url=_base_url(),
    auth_header_format="Bearer {api_key}",
)


def _token_type_header() -> str:
    return os.getenv("SNOWFLAKE_TOKEN_TYPE", "PROGRAMMATIC_ACCESS_TOKEN")


def _statement_context() -> dict[str, str]:
    ctx: dict[str, str] = {}
    for key, env in [
        ("warehouse", "SNOWFLAKE_WAREHOUSE"),
        ("database", "SNOWFLAKE_DATABASE"),
        ("schema", "SNOWFLAKE_SCHEMA"),
    ]:
        val = os.getenv(env, "")
        if val:
            ctx[key] = val
    return ctx


async def dispatch_sql(
    sql: str,
    *,
    max_rows: int = 100,
) -> tuple[list[str], list[list[Any]], str | None]:
    """Execute SQL via Snowflake SQL API. Returns (columns, rows_as_arrays, error)."""
    body: dict[str, Any] = {"statement": sql, "timeout": 60}
    body.update(_statement_context())

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Snowflake-Authorization-Token-Type": _token_type_header(),
    }

    ctx = get_context()
    req = HttpRequest(method=HttpMethod.POST, path="/api/v2/statements", body=body, headers=headers)
    resp = await ctx.dispatch(_CONN_NAME, req)

    if resp.error:
        return [], [], resp.error

    data = resp.body or {}

    code = str(data.get("code", ""))
    if code and code not in ("090001", "333001"):
        message = data.get("message", "Unknown SQL API error")
        return [], [], f"Snowflake error {code}: {message}"

    row_type = data.get("rowType", [])
    columns = [col["name"] for col in row_type] if row_type else []

    raw_rows = data.get("data", [])
    truncated = len(raw_rows) > max_rows
    rows = raw_rows[:max_rows]

    return columns, rows, None if code in ("090001", "333001", "") else data.get("message")
