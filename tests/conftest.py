from __future__ import annotations

import os

import pytest


def _has_snowflake_creds() -> bool:
    return bool(
        os.getenv("SNOWFLAKE_ACCOUNT")
        and os.getenv("SNOWFLAKE_USER")
        and (os.getenv("SNOWFLAKE_PASSWORD") or os.getenv("SNOWFLAKE_PRIVATE_KEY"))
    )


skip_without_creds = pytest.mark.skipif(
    not _has_snowflake_creds(),
    reason="Snowflake credentials not set (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD)",
)
