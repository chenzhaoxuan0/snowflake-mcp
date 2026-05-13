from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from snowflake_mcp import (
    describe_table,
    list_databases,
    list_schemas,
    list_tables,
    list_warehouses,
    run_query,
)
from snowflake_mcp.types import (
    DescribeTableResult,
    ListDatabasesResult,
    ListSchemasResult,
    ListTablesResult,
    ListWarehousesResult,
    QueryResult,
)


def _mock_execute(return_value):
    """Build a mock for transport.get_client().execute() returning the given rows."""
    mock_client = MagicMock()
    mock_client.execute.return_value = return_value
    return mock_client


# --- list_databases ---


@pytest.mark.asyncio
async def test_list_databases_success():
    mock_client = _mock_execute(
        (
            ["name", "created_on", "retention_time"],
            [
                {"name": "DB1", "created_on": "2024-01-01", "retention_time": "1"},
                {"name": "DB2", "created_on": "2024-02-01", "retention_time": "1"},
            ],
            False,
        )
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await list_databases()

    assert isinstance(result, ListDatabasesResult)
    assert result.success
    assert len(result.databases) == 2
    assert result.databases[0].name == "DB1"


@pytest.mark.asyncio
async def test_list_databases_error():
    mock_client = MagicMock()
    mock_client.execute.side_effect = ConnectionError("connection failed")
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await list_databases()

    assert not result.success
    assert "connection failed" in result.error


# --- list_schemas ---


@pytest.mark.asyncio
async def test_list_schemas_with_database():
    mock_client = _mock_execute(
        (
            ["name", "database_name", "created_on"],
            [{"name": "PUBLIC", "database_name": "MYDB", "created_on": "2024-01-01"}],
            False,
        )
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await list_schemas(database="MYDB")

    assert isinstance(result, ListSchemasResult)
    assert result.success
    assert len(result.schemas) == 1
    assert result.schemas[0].name == "PUBLIC"


# --- list_tables ---


@pytest.mark.asyncio
async def test_list_tables_with_db_and_schema():
    mock_client = _mock_execute(
        (
            ["name", "database_name", "schema_name", "kind", "rows"],
            [{"name": "USERS", "database_name": "DB", "schema_name": "SCH", "kind": "TABLE", "rows": "100"}],
            False,
        )
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await list_tables(database="DB", schema="SCH")

    assert isinstance(result, ListTablesResult)
    assert result.success
    assert result.tables[0].name == "USERS"
    assert result.tables[0].kind == "TABLE"


# --- describe_table ---


@pytest.mark.asyncio
async def test_describe_table():
    mock_client = _mock_execute(
        (
            ["name", "type", "null?", "default", "pk"],
            [
                {"name": "ID", "type": "NUMBER(38,0)", "null?": "N", "default": "", "pk": "Y"},
                {"name": "NAME", "type": "VARCHAR(100)", "null?": "Y", "default": "", "pk": "N"},
            ],
            False,
        )
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await describe_table(table="USERS", database="DB", schema="SCH")

    assert isinstance(result, DescribeTableResult)
    assert result.success
    assert len(result.columns) == 2
    assert result.columns[0].name == "ID"
    assert result.columns[0].pk == "Y"


# --- run_query ---


@pytest.mark.asyncio
async def test_run_query_select_success():
    mock_client = _mock_execute(
        (
            ["ID", "NAME"],
            [{"ID": 1, "NAME": "Alice"}],
            False,
        )
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
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
    mock_client = _mock_execute(
        (["status"], [{"status": "inserted"}], False)
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
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
    mock_client = _mock_execute(
        (["name"], [{"name": "DB1"}], False)
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await run_query(sql="SHOW DATABASES")

    assert result.success


@pytest.mark.asyncio
async def test_run_query_truncated():
    mock_client = _mock_execute(
        (["ID"], [{"ID": i} for i in range(5)], True)
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await run_query(sql="SELECT * FROM big_table")

    assert result.truncated is True


# --- list_warehouses ---


@pytest.mark.asyncio
async def test_list_warehouses():
    mock_client = _mock_execute(
        (
            ["name", "state", "size"],
            [
                {"name": "COMPUTE_WH", "state": "STARTED", "size": "X-Small"},
                {"name": "LOAD_WH", "state": "SUSPENDED", "size": "Small"},
            ],
            False,
        )
    )
    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        result = await list_warehouses()

    assert isinstance(result, ListWarehousesResult)
    assert result.success
    assert len(result.warehouses) == 2
    assert result.warehouses[0].name == "COMPUTE_WH"
    assert result.warehouses[1].state == "SUSPENDED"
