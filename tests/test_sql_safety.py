from __future__ import annotations

import pytest

from snowflake_mcp.sql_safety import (
    build_qualified_name,
    is_read_only_sql,
    quote_identifier,
)

# --- is_read_only_sql ---


class TestIsReadOnlySql:
    # Allowed read statements
    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM t",
            "select id from users",
            "  SELECT 1",
            "WITH cte AS (SELECT 1) SELECT * FROM cte",
            "SHOW DATABASES",
            "SHOW SCHEMAS IN DATABASE mydb",
            "SHOW TABLES",
            "DESCRIBE TABLE mytable",
            "DESC TABLE mytable",
            "EXPLAIN SELECT * FROM t",
            "USE DATABASE mydb",
            "SHOW WAREHOUSES",
        ],
    )
    def test_read_statements_allowed(self, sql: str) -> None:
        assert is_read_only_sql(sql) is True

    # Rejected write statements
    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO t VALUES (1)",
            "UPDATE t SET x = 1",
            "DELETE FROM t",
            "MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.x = s.x",
            "CREATE TABLE t (id INT)",
            "ALTER TABLE t ADD COLUMN x INT",
            "DROP TABLE t",
            "TRUNCATE TABLE t",
            "COPY INTO t FROM @stage",
            "GRANT SELECT ON t TO role",
            "REVOKE SELECT ON t FROM role",
            "RENAME TABLE t TO t2",
            "COMMENT ON TABLE t IS 'test'",
        ],
    )
    def test_write_statements_rejected(self, sql: str) -> None:
        assert is_read_only_sql(sql) is False

    def test_multi_statement_with_write_rejected(self) -> None:
        sql = "SELECT 1; INSERT INTO t VALUES (1)"
        assert is_read_only_sql(sql) is False

    def test_multi_statement_all_read_allowed(self) -> None:
        sql = "SELECT 1; SELECT 2"
        assert is_read_only_sql(sql) is True

    def test_empty_string_rejected(self) -> None:
        assert is_read_only_sql("") is False
        assert is_read_only_sql("   ") is False

    def test_semicolon_trailing_read(self) -> None:
        assert is_read_only_sql("SELECT 1;") is True

    def test_mixed_case_prefix(self) -> None:
        assert is_read_only_sql("SeLeCt * FROM t") is True
        assert is_read_only_sql("InSeRt INTO t VALUES (1)") is False


# --- quote_identifier ---


class TestQuoteIdentifier:
    def test_simple_name(self) -> None:
        assert quote_identifier("mytable") == '"mytable"'

    def test_name_with_spaces(self) -> None:
        assert quote_identifier("my table") == '"my table"'

    def test_name_with_quotes_escaped(self) -> None:
        assert quote_identifier('my"table') == '"my""table"'

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            quote_identifier("")

    def test_sql_comment_injection_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid identifier"):
            quote_identifier("t; DROP TABLE users")

    def test_block_comment_injection_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid identifier"):
            quote_identifier("t/**/")

    def test_whitespace_stripped(self) -> None:
        assert quote_identifier("  mytable  ") == '"mytable"'


# --- build_qualified_name ---


class TestBuildQualifiedName:
    def test_full_three_part(self) -> None:
        result = build_qualified_name("db", "sch", "tbl")
        assert result == '"db"."sch"."tbl"'

    def test_two_part(self) -> None:
        result = build_qualified_name(None, "sch", "tbl")
        assert result == '"sch"."tbl"'

    def test_single_part(self) -> None:
        result = build_qualified_name(None, None, "tbl")
        assert result == '"tbl"'

    def test_empty_all_rejected(self) -> None:
        with pytest.raises(ValueError, match="At least one"):
            build_qualified_name(None, None, None)
