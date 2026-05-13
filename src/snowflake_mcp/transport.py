from __future__ import annotations

import os
from typing import Any

import snowflake.connector


def _sanitize_error(msg: str) -> str:
    """Remove credential-like patterns from error messages."""
    for var in (
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_PRIVATE_KEY",
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
    ):
        val = os.getenv(var, "")
        if val and val in msg:
            msg = msg.replace(val, f"<{var}>")
    return msg


class SnowflakeClient:
    """Thin wrapper around snowflake.connector with centralized credential reads."""

    def __init__(self) -> None:
        self._account: str | None = None
        self._user: str | None = None
        self._warehouse: str | None = None
        self._database: str | None = None
        self._schema: str | None = None

    def _connect_kwargs(self) -> dict[str, Any]:
        self._account = os.getenv("SNOWFLAKE_ACCOUNT", "")
        self._user = os.getenv("SNOWFLAKE_USER", "")
        self._warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        self._database = os.getenv("SNOWFLAKE_DATABASE")
        self._schema = os.getenv("SNOWFLAKE_SCHEMA")

        kwargs: dict[str, Any] = {
            "account": self._account,
            "user": self._user,
        }

        password = os.getenv("SNOWFLAKE_PASSWORD", "")
        private_key = os.getenv("SNOWFLAKE_PRIVATE_KEY", "")

        if password:
            kwargs["password"] = password
        elif private_key:
            kwargs["private_key"] = private_key
        else:
            raise ValueError("SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY is required")

        if self._warehouse:
            kwargs["warehouse"] = self._warehouse
        if self._database:
            kwargs["database"] = self._database
        if self._schema:
            kwargs["schema"] = self._schema

        return kwargs

    def execute(
        self,
        sql: str,
        *,
        max_rows: int = 100,
    ) -> tuple[list[str], list[dict[str, Any]], bool]:
        """Execute SQL and return (columns, rows_as_dicts, truncated).

        Raises on connection or execution errors with sanitized messages.
        """
        kwargs = self._connect_kwargs()
        try:
            conn = snowflake.connector.connect(**kwargs)
        except Exception as exc:
            raise ConnectionError(_sanitize_error(str(exc))) from exc

        try:
            cur = conn.cursor(snowflake.connector.DictCursor)
            try:
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                all_rows = cur.fetchall()
                truncated = len(all_rows) > max_rows
                rows = all_rows[:max_rows]
                return columns, rows, truncated
            finally:
                cur.close()
        except Exception as exc:
            raise RuntimeError(_sanitize_error(str(exc))) from exc
        finally:
            conn.close()


# Module-level singleton
_client: SnowflakeClient | None = None


def get_client() -> SnowflakeClient:
    global _client
    if _client is None:
        _client = SnowflakeClient()
    return _client
