from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from snowflake_mcp.transport import _base_url, _statement_context, _token_type_header, snowflake_conn


class TestBaseUrl:
    def test_derives_from_account(self) -> None:
        with patch.dict("os.environ", {"SNOWFLAKE_ACCOUNT": "xy12345.us-east-1"}):
            assert _base_url() == "https://xy12345.us-east-1.snowflakecomputing.com"

    def test_default_when_missing(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("SNOWFLAKE_ACCOUNT", None)
            assert "snowflakecomputing.com" in _base_url()


class TestTokenTypeHeader:
    def test_default_pat(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("SNOWFLAKE_TOKEN_TYPE", None)
            assert _token_type_header() == "PROGRAMMATIC_ACCESS_TOKEN"

    def test_custom_type(self) -> None:
        with patch.dict("os.environ", {"SNOWFLAKE_TOKEN_TYPE": "OAUTH"}):
            assert _token_type_header() == "OAUTH"


class TestStatementContext:
    def test_returns_env_values(self) -> None:
        with patch.dict(
            "os.environ",
            {"SNOWFLAKE_WAREHOUSE": "WH", "SNOWFLAKE_DATABASE": "DB", "SNOWFLAKE_SCHEMA": "SCH"},
            clear=False,
        ):
            ctx = _statement_context()
            assert ctx == {"warehouse": "WH", "database": "DB", "schema": "SCH"}

    def test_omits_missing(self) -> None:
        with patch.dict("os.environ", {"SNOWFLAKE_WAREHOUSE": "WH"}, clear=False):
            import os
            os.environ.pop("SNOWFLAKE_DATABASE", None)
            os.environ.pop("SNOWFLAKE_SCHEMA", None)
            ctx = _statement_context()
            assert "database" not in ctx
            assert "schema" not in ctx


class TestConnection:
    def test_connection_uses_token_secret(self) -> None:
        assert snowflake_conn.name == "snowflake"

    def test_connection_bearer_format(self) -> None:
        assert "Bearer" in snowflake_conn.auth_header_format


class TestDispatchSql:
    @pytest.mark.asyncio
    async def test_dispatch_parses_sql_api_response(self) -> None:
        mock_resp = MagicMock()
        mock_resp.error = None
        mock_resp.body = {
            "code": "090001",
            "rowType": [{"name": "NAME"}, {"name": "CREATED_ON"}],
            "data": [["DB1", "2024-01-01"], ["DB2", "2024-02-01"]],
        }

        mock_ctx = MagicMock()
        mock_ctx.dispatch = AsyncMock(return_value=mock_resp)

        with patch("snowflake_mcp.transport.get_context", return_value=mock_ctx):
            from snowflake_mcp.transport import dispatch_sql
            columns, rows, err = await dispatch_sql("SHOW DATABASES")

        assert err is None
        assert columns == ["NAME", "CREATED_ON"]
        assert len(rows) == 2
        assert rows[0] == ["DB1", "2024-01-01"]

    @pytest.mark.asyncio
    async def test_dispatch_returns_error(self) -> None:
        mock_resp = MagicMock()
        mock_resp.error = "Unauthorized"
        mock_resp.body = {}

        mock_ctx = MagicMock()
        mock_ctx.dispatch = AsyncMock(return_value=mock_resp)

        with patch("snowflake_mcp.transport.get_context", return_value=mock_ctx):
            from snowflake_mcp.transport import dispatch_sql
            columns, rows, err = await dispatch_sql("SELECT 1")

        assert err == "Unauthorized"
        assert columns == []
        assert rows == []

    @pytest.mark.asyncio
    async def test_dispatch_truncates_rows(self) -> None:
        mock_resp = MagicMock()
        mock_resp.error = None
        mock_resp.body = {
            "code": "090001",
            "rowType": [{"name": "ID"}],
            "data": [[i] for i in range(200)],
        }

        mock_ctx = MagicMock()
        mock_ctx.dispatch = AsyncMock(return_value=mock_resp)

        with patch("snowflake_mcp.transport.get_context", return_value=mock_ctx):
            from snowflake_mcp.transport import dispatch_sql
            columns, rows, err = await dispatch_sql("SELECT 1", max_rows=100)

        assert len(rows) == 100
