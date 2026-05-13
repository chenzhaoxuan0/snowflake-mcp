from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DatabaseSummary:
    name: str = ""
    created: str = ""
    retention_time: str = ""

    @classmethod
    def from_row(cls, row: dict[str, Any] | tuple[Any, ...], columns: list[str] | None = None) -> DatabaseSummary:
        d = _to_dict(row, columns)
        return cls(
            name=str(d.get("name", d.get("NAME", ""))),
            created=str(d.get("created_on", d.get("CREATED_ON", ""))),
            retention_time=str(d.get("retention_time", d.get("RETENTION_TIME", ""))),
        )


@dataclass(frozen=True)
class SchemaSummary:
    name: str = ""
    database: str = ""
    created: str = ""

    @classmethod
    def from_row(cls, row: dict[str, Any] | tuple[Any, ...], columns: list[str] | None = None) -> SchemaSummary:
        d = _to_dict(row, columns)
        return cls(
            name=str(d.get("name", d.get("NAME", ""))),
            database=str(d.get("database_name", d.get("DATABASE_NAME", ""))),
            created=str(d.get("created_on", d.get("CREATED_ON", ""))),
        )


@dataclass(frozen=True)
class TableSummary:
    name: str = ""
    database: str = ""
    schema: str = ""
    kind: str = ""
    rows: str = ""

    @classmethod
    def from_row(cls, row: dict[str, Any] | tuple[Any, ...], columns: list[str] | None = None) -> TableSummary:
        d = _to_dict(row, columns)
        return cls(
            name=str(d.get("name", d.get("NAME", ""))),
            database=str(d.get("database_name", d.get("DATABASE_NAME", ""))),
            schema=str(d.get("schema_name", d.get("SCHEMA_NAME", ""))),
            kind=str(d.get("kind", d.get("KIND", ""))),
            rows=str(d.get("rows", d.get("ROWS", ""))),
        )


@dataclass(frozen=True)
class ColumnSummary:
    name: str = ""
    type: str = ""
    nullable: str = ""
    default: str = ""
    pk: str = ""

    @classmethod
    def from_row(cls, row: dict[str, Any] | tuple[Any, ...], columns: list[str] | None = None) -> ColumnSummary:
        d = _to_dict(row, columns)
        return cls(
            name=str(d.get("name", d.get("NAME", ""))),
            type=str(d.get("type", d.get("TYPE", ""))),
            nullable=str(d.get("null?", d.get("NULL?", d.get("NULLABLE", "")))),
            default=str(d.get("default", d.get("DEFAULT", ""))),
            pk=str(d.get("pk", d.get("PK", ""))),
        )


@dataclass(frozen=True)
class WarehouseSummary:
    name: str = ""
    state: str = ""
    size: str = ""

    @classmethod
    def from_row(cls, row: dict[str, Any] | tuple[Any, ...], columns: list[str] | None = None) -> WarehouseSummary:
        d = _to_dict(row, columns)
        return cls(
            name=str(d.get("name", d.get("NAME", ""))),
            state=str(d.get("state", d.get("STATE", ""))),
            size=str(d.get("size", d.get("SIZE", ""))),
        )


@dataclass(frozen=True)
class QueryResult:
    success: bool = False
    error: str | None = None
    rows: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    statement: str = ""
    warning: str | None = None


@dataclass(frozen=True)
class ListDatabasesResult:
    success: bool = False
    error: str | None = None
    databases: list[DatabaseSummary] = field(default_factory=list)


@dataclass(frozen=True)
class ListSchemasResult:
    success: bool = False
    error: str | None = None
    schemas: list[SchemaSummary] = field(default_factory=list)


@dataclass(frozen=True)
class ListTablesResult:
    success: bool = False
    error: str | None = None
    tables: list[TableSummary] = field(default_factory=list)


@dataclass(frozen=True)
class DescribeTableResult:
    success: bool = False
    error: str | None = None
    columns: list[ColumnSummary] = field(default_factory=list)


@dataclass(frozen=True)
class ListWarehousesResult:
    success: bool = False
    error: str | None = None
    warehouses: list[WarehouseSummary] = field(default_factory=list)


def _to_dict(row: dict[str, Any] | tuple[Any, ...], columns: list[str] | None) -> dict[str, Any]:
    if isinstance(row, dict):
        return row
    if columns is None:
        return {}
    return dict(zip(columns, row))
