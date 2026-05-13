from __future__ import annotations

import os

import pytest

from conftest import skip_without_creds


@pytest.mark.asyncio
@skip_without_creds
async def test_list_databases_live():
    from snowflake_mcp import list_databases

    result = await list_databases()
    assert result.success, f"Failed: {result.error}"
    assert len(result.databases) > 0


@pytest.mark.asyncio
@skip_without_creds
async def test_list_warehouses_live():
    from snowflake_mcp import list_warehouses

    result = await list_warehouses()
    assert result.success, f"Failed: {result.error}"


@pytest.mark.asyncio
@skip_without_creds
async def test_run_query_select_live():
    from snowflake_mcp import run_query

    result = await run_query(sql="SELECT CURRENT_VERSION() AS ver")
    assert result.success, f"Failed: {result.error}"
    assert result.row_count >= 1
