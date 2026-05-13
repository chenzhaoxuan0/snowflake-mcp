from __future__ import annotations

import re

_READ_PREFIXES = (
    "SELECT",
    "WITH",
    "SHOW",
    "DESCRIBE",
    "DESC",
    "EXPLAIN",
    "USE",
)

_WRITE_PREFIXES = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "COPY",
    "GRANT",
    "REVOKE",
    "RENAME",
    "COMMENT",
    "UNDROP",
)

_PREFIX_RE = re.compile(r"^\s*([A-Za-z]+)")


def is_read_only_sql(sql: str) -> bool:
    """Return True if every statement in *sql* is read-only."""
    if not sql or not sql.strip():
        return False
    for stmt in _split_statements(sql):
        prefix = _extract_prefix(stmt)
        if not prefix:
            return False
        if prefix.upper() not in _READ_PREFIXES:
            return False
    return True


def _split_statements(sql: str) -> list[str]:
    """Split on semicolons, ignoring trailing empty segments."""
    parts = sql.split(";")
    return [p for p in parts if p.strip()]


def _extract_prefix(stmt: str) -> str:
    m = _PREFIX_RE.match(stmt)
    return m.group(1) if m else ""


def quote_identifier(name: str) -> str:
    """Quote a Snowflake identifier, escaping any internal double quotes."""
    if not name:
        raise ValueError("Identifier must not be empty")
    # Strip leading/trailing whitespace
    name = name.strip()
    # Reject obvious injection attempts
    if "--" in name or "/*" in name or "*/" in name or ";" in name:
        raise ValueError(f"Invalid identifier: {name!r}")
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def build_qualified_name(database: str | None, schema: str | None, table: str | None) -> str:
    """Build a dot-separated qualified identifier like db.schema.table."""
    parts: list[str] = []
    if database:
        parts.append(quote_identifier(database))
    if schema:
        parts.append(quote_identifier(schema))
    if table:
        parts.append(quote_identifier(table))
    if not parts:
        raise ValueError("At least one identifier is required")
    return ".".join(parts)
