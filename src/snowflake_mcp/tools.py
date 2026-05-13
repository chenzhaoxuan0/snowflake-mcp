from __future__ import annotations

from typing import Any

from dedalus_mcp import tool
from dedalus_mcp.types import ToolAnnotations

from snowflake_mcp.sql_safety import (
    build_qualified_name,
    is_read_only_sql,
    quote_identifier,
)
from snowflake_mcp.transport import _sanitize_error, get_client
from snowflake_mcp.types import (
    ColumnSummary,
    DatabaseSummary,
    DescribeTableResult,
    ListDatabasesResult,
    ListSchemasResult,
    ListTablesResult,
    ListWarehousesResult,
    QueryResult,
    SchemaSummary,
    TableSummary,
    WarehouseSummary,
)


def _execute(sql: str, *, max_rows: int = 100) -> tuple[list[str], list[dict[str, Any]], bool]:
    return get_client().execute(sql, max_rows=max_rows)


def _safe_execute(sql: str, *, max_rows: int = 100) -> tuple[list[str], list[dict[str, Any]], bool] | str:
    """Execute with error handling. Returns (columns, rows, truncated) or error string."""
    try:
        return _execute(sql, max_rows=max_rows)
    except (ConnectionError, RuntimeError) as exc:
        return _sanitize_error(str(exc))


# --- Tools ---


@tool(
    description="List Snowflake databases",
    tags=["snowflake", "databases", "list"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_databases() -> ListDatabasesResult:
    result = _safe_execute("SHOW DATABASES")
    if isinstance(result, str):
        return ListDatabasesResult(success=False, error=result)
    columns, rows, _ = result
    return ListDatabasesResult(
        success=True,
        databases=[DatabaseSummary.from_row(r, columns) for r in rows],
    )


@tool(
    description="List schemas in a Snowflake database",
    tags=["snowflake", "schemas", "list"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_schemas(database: str = "") -> ListSchemasResult:
    if database:
        sql = f"SHOW SCHEMAS IN DATABASE {quote_identifier(database)}"
    else:
        sql = "SHOW SCHEMAS IN CURRENT DATABASE()"
    result = _safe_execute(sql)
    if isinstance(result, str):
        return ListSchemasResult(success=False, error=result)
    columns, rows, _ = result
    return ListSchemasResult(
        success=True,
        schemas=[SchemaSummary.from_row(r, columns) for r in rows],
    )


@tool(
    description="List tables in a Snowflake schema",
    tags=["snowflake", "tables", "list"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_tables(database: str = "", schema: str = "") -> ListTablesResult:
    if database and schema:
        qualified = f"{quote_identifier(database)}.{quote_identifier(schema)}"
        sql = f"SHOW TABLES IN SCHEMA {qualified}"
    elif database:
        sql = f"SHOW TABLES IN DATABASE {quote_identifier(database)}"
    else:
        sql = "SHOW TABLES IN CURRENT SCHEMA()"
    result = _safe_execute(sql)
    if isinstance(result, str):
        return ListTablesResult(success=False, error=result)
    columns, rows, _ = result
    return ListTablesResult(
        success=True,
        tables=[TableSummary.from_row(r, columns) for r in rows],
    )


@tool(
    description="Describe columns of a Snowflake table",
    tags=["snowflake", "table", "describe"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def describe_table(
    table: str,
    database: str = "",
    schema: str = "",
) -> DescribeTableResult:
    if database and schema:
        qualified = build_qualified_name(database, schema, table)
    else:
        qualified = quote_identifier(table)
    sql = f"DESCRIBE TABLE {qualified}"
    result = _safe_execute(sql)
    if isinstance(result, str):
        return DescribeTableResult(success=False, error=result)
    columns, rows, _ = result
    return DescribeTableResult(
        success=True,
        columns=[ColumnSummary.from_row(r, columns) for r in rows],
    )


@tool(
    description="Run a SQL query against Snowflake. SELECT-only by default; set allow_writes=True to enable DML.",
    tags=["snowflake", "query", "sql"],
)
async def run_query(
    sql: str,
    allow_writes: bool = False,
    max_rows: int = 100,
) -> QueryResult:
    max_rows = min(max(max_rows, 1), 1000)
    if not sql.strip():
        return QueryResult(success=False, error="SQL must not be empty")

    if not allow_writes and not is_read_only_sql(sql):
        return QueryResult(
            success=False,
            error="Statement is not read-only. Set allow_writes=True to enable DML statements.",
        )

    warning = None
    if allow_writes:
        warning = "allow_writes=True: query may modify data"

    result = _safe_execute(sql, max_rows=max_rows)
    if isinstance(result, str):
        return QueryResult(success=False, error=result, statement=sql)
    columns, rows, truncated = result
    return QueryResult(
        success=True,
        rows=rows,
        columns=columns,
        row_count=len(rows),
        truncated=truncated,
        statement=sql,
        warning=warning,
    )


@tool(
    description="List Snowflake warehouses",
    tags=["snowflake", "warehouses", "list"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_warehouses() -> ListWarehousesResult:
    result = _safe_execute("SHOW WAREHOUSES")
    if isinstance(result, str):
        return ListWarehousesResult(success=False, error=result)
    columns, rows, _ = result
    return ListWarehousesResult(
        success=True,
        warehouses=[WarehouseSummary.from_row(r, columns) for r in rows],
    )
