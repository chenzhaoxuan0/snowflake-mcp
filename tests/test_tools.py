from __future__ import annotations

from unittest.mock import patch

import pytest

from snowflake_mcp import (
    describe_table,
    list_databases,
    list_schemas,
    list_tables,
    list_warehouses,
    run_query,
    smoke_ping,
)
from snowflake_mcp.types import (
    DescribeTableResult,
    ListDatabasesResult,
    ListSchemasResult,
    ListTablesResult,
    ListWarehousesResult,
    QueryResult,
)


async def _mock_dispatch(sql, *, max_rows=100):
    """Override me in subtests."""
    return [], [], "not mocked"


@pytest.fixture(autouse=True)
def _patch_dispatch(self=None):
    async def _noop(sql, **kw):
        return [], [], "not mocked"

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=_noop):
        yield


@pytest.mark.asyncio
async def test_smoke_ping_echoes_message():
    result = await smoke_ping(message="snowflake-check")

    assert result.ok
    assert result.message == "snowflake-check"


# --- list_databases ---


@pytest.mark.asyncio
async def test_list_databases_success():
    async def fake_dispatch(sql, **kw):
        columns = ["created_on", "name", "retention_time"]
        rows = [
            ["2024-01-01", "DB1", "1"],
            ["2024-02-01", "DB2", "1"],
        ]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await list_databases()

    assert isinstance(result, ListDatabasesResult)
    assert result.success
    assert len(result.databases) == 2
    assert result.databases[0].name == "DB1"


@pytest.mark.asyncio
async def test_list_databases_error():
    async def fake_dispatch(sql, **kw):
        return [], [], "forbidden"

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await list_databases()

    assert not result.success
    assert "forbidden" in result.error


# --- list_schemas ---


@pytest.mark.asyncio
async def test_list_schemas_with_database():
    async def fake_dispatch(sql, **kw):
        assert "MYDB" in sql
        columns = ["created_on", "database_name", "name"]
        rows = [["2024-01-01", "MYDB", "PUBLIC"]]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await list_schemas(database="MYDB")

    assert isinstance(result, ListSchemasResult)
    assert result.success
    assert result.schemas[0].name == "PUBLIC"


# --- list_tables ---


@pytest.mark.asyncio
async def test_list_tables_with_db_and_schema():
    async def fake_dispatch(sql, **kw):
        columns = ["database_name", "schema_name", "name", "kind", "rows"]
        rows = [["DB", "SCH", "USERS", "TABLE", "100"]]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await list_tables(database="DB", schema="SCH")

    assert isinstance(result, ListTablesResult)
    assert result.success
    assert result.tables[0].name == "USERS"
    assert result.tables[0].kind == "TABLE"


# --- describe_table ---


@pytest.mark.asyncio
async def test_describe_table():
    async def fake_dispatch(sql, **kw):
        assert "DESCRIBE" in sql
        columns = ["name", "type", "null?", "default", "pk"]
        rows = [
            ["ID", "NUMBER(38,0)", "N", "", "Y"],
            ["NAME", "VARCHAR(100)", "Y", "", "N"],
        ]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await describe_table(table="USERS", database="DB", schema="SCH")

    assert isinstance(result, DescribeTableResult)
    assert result.success
    assert len(result.columns) == 2
    assert result.columns[0].name == "ID"
    assert result.columns[0].pk == "Y"


# --- run_query ---


@pytest.mark.asyncio
async def test_run_query_select_success():
    async def fake_dispatch(sql, **kw):
        columns = ["ID", "NAME"]
        rows = [[1, "Alice"]]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await run_query(sql="SELECT * FROM users")

    assert isinstance(result, QueryResult)
    assert result.success
    assert result.row_count == 1
    assert result.rows[0]["NAME"] == "Alice"
    assert not result.truncated


@pytest.mark.asyncio
async def test_run_query_empty_rejected():
    result = await run_query(sql="   ")

    assert not result.success
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_run_query_write_rejected_by_default():
    result = await run_query(sql="INSERT INTO t VALUES (1)")

    assert not result.success
    assert "not read-only" in result.error


@pytest.mark.asyncio
async def test_run_query_write_allowed_with_flag():
    async def fake_dispatch(sql, **kw):
        columns = ["status"]
        rows = [["inserted"]]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await run_query(sql="INSERT INTO t VALUES (1)", allow_writes=True)

    assert isinstance(result, QueryResult)
    assert result.success
    assert result.warning is not None
    assert "allow_writes" in result.warning


@pytest.mark.asyncio
async def test_run_query_multi_statement_write_rejected():
    result = await run_query(sql="SELECT 1; DROP TABLE users")

    assert not result.success


@pytest.mark.asyncio
async def test_run_query_show_allowed():
    async def fake_dispatch(sql, **kw):
        columns = ["name"]
        rows = [["DB1"]]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await run_query(sql="SHOW DATABASES")

    assert result.success


@pytest.mark.asyncio
async def test_run_query_truncated():
    async def fake_dispatch(sql, *, max_rows=100):
        columns = ["ID"]
        rows = [[i] for i in range(150)]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await run_query(sql="SELECT * FROM big_table")

    assert result.truncated is True
    assert result.row_count == 100


# --- list_warehouses ---


@pytest.mark.asyncio
async def test_list_warehouses():
    async def fake_dispatch(sql, **kw):
        assert "SHOW WAREHOUSES" in sql
        columns = ["name", "state", "size"]
        rows = [
            ["COMPUTE_WH", "STARTED", "X-Small"],
            ["LOAD_WH", "SUSPENDED", "Small"],
        ]
        return columns, rows, None

    with patch("snowflake_mcp.tools.dispatch_sql", side_effect=fake_dispatch):
        result = await list_warehouses()

    assert isinstance(result, ListWarehousesResult)
    assert result.success
    assert len(result.warehouses) == 2
    assert result.warehouses[0].name == "COMPUTE_WH"
    assert result.warehouses[1].state == "SUSPENDED"
