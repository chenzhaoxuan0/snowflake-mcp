from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from snowflake_mcp.transport import SnowflakeClient, _sanitize_error


class TestSanitizeError:
    def test_removes_password_from_error(self) -> None:
        with patch.dict("os.environ", {"SNOWFLAKE_PASSWORD": "secret123"}, clear=False):
            msg = _sanitize_error("Login failed for password=secret123")
            assert "secret123" not in msg
            assert "<SNOWFLAKE_PASSWORD>" in msg

    def test_no_env_var_returns_original(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            # Remove the var if it exists
            import os
            os.environ.pop("SNOWFLAKE_PASSWORD", None)
            msg = _sanitize_error("some generic error")
            assert msg == "some generic error"


class TestSnowflakeClient:
    def test_missing_credentials_raises(self) -> None:
        client = SnowflakeClient()
        with patch.dict("os.environ", {}, clear=False):
            import os
            for k in ["SNOWFLAKE_PASSWORD", "SNOWFLAKE_PRIVATE_KEY"]:
                os.environ.pop(k, None)
            with pytest.raises(ValueError, match="SNOWFLAKE_PASSWORD"):
                client._connect_kwargs()

    def test_password_auth_populated(self) -> None:
        client = SnowflakeClient()
        with patch.dict(
            "os.environ",
            {
                "SNOWFLAKE_ACCOUNT": "test.us-east-1",
                "SNOWFLAKE_USER": "admin",
                "SNOWFLAKE_PASSWORD": "pass",
                "SNOWFLAKE_WAREHOUSE": "WH",
            },
            clear=False,
        ):
            kwargs = client._connect_kwargs()
            assert kwargs["account"] == "test.us-east-1"
            assert kwargs["user"] == "admin"
            assert kwargs["password"] == "pass"
            assert kwargs["warehouse"] == "WH"

    def test_execute_returns_columns_and_rows(self) -> None:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.description = [("ID",), ("NAME",)]
        mock_cur.fetchall.return_value = [{"ID": 1, "NAME": "Alice"}]
        mock_conn.cursor.return_value = mock_cur

        client = SnowflakeClient()
        with patch("snowflake_mcp.transport.snowflake.connector.connect", return_value=mock_conn):
            with patch.dict(
                "os.environ",
                {"SNOWFLAKE_ACCOUNT": "a", "SNOWFLAKE_USER": "u", "SNOWFLAKE_PASSWORD": "p"},
                clear=False,
            ):
                columns, rows, truncated = client.execute("SELECT 1")

        assert columns == ["ID", "NAME"]
        assert len(rows) == 1
        assert rows[0]["NAME"] == "Alice"
        assert not truncated

    def test_execute_truncates_large_results(self) -> None:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.description = [("ID",)]
        mock_cur.fetchall.return_value = [{"ID": i} for i in range(150)]
        mock_conn.cursor.return_value = mock_cur

        client = SnowflakeClient()
        with patch("snowflake_mcp.transport.snowflake.connector.connect", return_value=mock_conn):
            with patch.dict(
                "os.environ",
                {"SNOWFLAKE_ACCOUNT": "a", "SNOWFLAKE_USER": "u", "SNOWFLAKE_PASSWORD": "p"},
                clear=False,
            ):
                columns, rows, truncated = client.execute("SELECT 1", max_rows=100)

        assert truncated is True
        assert len(rows) == 100

    def test_execute_sanitizes_connection_error(self) -> None:
        import snowflake.connector

        with patch(
            "snowflake_mcp.transport.snowflake.connector.connect",
            side_effect=snowflake.connector.Error("Failed for user=mysecretuser@host"),
        ):
            client = SnowflakeClient()
            with patch.dict(
                "os.environ",
                {
                    "SNOWFLAKE_ACCOUNT": "a",
                    "SNOWFLAKE_USER": "mysecretuser@host",
                    "SNOWFLAKE_PASSWORD": "p",
                },
                clear=False,
            ):
                with pytest.raises(ConnectionError) as exc_info:
                    client.execute("SELECT 1")
                # The error should be sanitized
                assert "mysecretuser@host" not in str(exc_info.value) or "<SNOWFLAKE_USER>" in str(
                    exc_info.value
                )
