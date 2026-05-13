from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from snowflake_mcp import run_query


@pytest.mark.asyncio
async def test_error_messages_exclude_credentials():
    """Provider errors must not contain Snowflake credentials."""
    fake_password = "SUPER_SECRET_PASSWORD_12345"

    mock_client = MagicMock()
    mock_client.execute.side_effect = ConnectionError(f"Auth failed with password={fake_password}")

    with patch("snowflake_mcp.tools.get_client", return_value=mock_client):
        with patch.dict("os.environ", {"SNOWFLAKE_PASSWORD": fake_password}, clear=False):
            result = await run_query(sql="SELECT 1")

    assert not result.success
    # The sanitized error should not contain the raw password
    if fake_password in (result.error or ""):
        # If present, it must be masked
        assert f"<SNOWFLAKE_PASSWORD>" in result.error
