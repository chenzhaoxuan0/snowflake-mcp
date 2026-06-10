from __future__ import annotations

from dedalus_mcp import tool
from dedalus_mcp.types import ToolAnnotations

from snowflake_mcp.sql_safety import (
    build_qualified_name,
    is_read_only_sql,
    quote_identifier,
)
from snowflake_mcp.transport import dispatch_sql
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
    rows_to_dicts,
)

# --- Tools ---


@tool(
    description="List Snowflake databases",
    tags=["snowflake", "databases", "list"],
    annotations=ToolAnnotations(readOnlyHint=True),
)
async def list_databases() -> ListDatabasesResult:
    columns, rows, err = await dispatch_sql("SHOW DATABASES")
    if err:
        return ListDatabasesResult(success=False, error=err)
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
    sql = f"SHOW SCHEMAS IN DATABASE {quote_identifier(database)}" if database else "SHOW SCHEMAS IN CURRENT DATABASE()"
    columns, rows, err = await dispatch_sql(sql)
    if err:
        return ListSchemasResult(success=False, error=err)
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
    columns, rows, err = await dispatch_sql(sql)
    if err:
        return ListTablesResult(success=False, error=err)
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
    qualified = build_qualified_name(database, schema, table) if database and schema else quote_identifier(table)
    sql = f"DESCRIBE TABLE {qualified}"
    columns, rows, err = await dispatch_sql(sql)
    if err:
        return DescribeTableResult(success=False, error=err)
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

    columns, raw_rows, err = await dispatch_sql(sql, max_rows=max_rows)
    if err:
        return QueryResult(success=False, error=err, statement=sql)

    truncated = len(raw_rows) > max_rows
    dict_rows = rows_to_dicts(columns, raw_rows[:max_rows])

    return QueryResult(
        success=True,
        rows=dict_rows,
        columns=columns,
        row_count=len(dict_rows),
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
    columns, rows, err = await dispatch_sql("SHOW WAREHOUSES")
    if err:
        return ListWarehousesResult(success=False, error=err)
    return ListWarehousesResult(
        success=True,
        warehouses=[WarehouseSummary.from_row(r, columns) for r in rows],
    )
