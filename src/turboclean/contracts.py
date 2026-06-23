from __future__ import annotations

import enum
from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

import polars
import pyarrow as pa

T = TypeVar("T", covariant=True)

class FileFormat(enum.Enum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    AVRO = "avro"
    EXCEL = "excel"
    XML = "xml"
    SQL = "sql"

@runtime_checkable
class Connector(Protocol):
    """Protocol for SQLAlchemy-compatible database connections."""
    def execute(self, query: str) -> Any: ...
    @property
    def dialect(self) -> str: ...

class CleanseRule(Protocol):
    """Independent cleansing rule with an apply method."""
    name: str
    column: str
    parameters: dict[str, Any]

    def apply(self, lf: polars.LazyFrame) -> polars.LazyFrame: ...

class DataProfile(Protocol):
    """Full statistical profile of a dataset."""
    schema: pa.Schema
    column_profiles: Mapping[str, ColumnProfile]   

    def summary(self) -> str: ...

class ColumnProfile(Protocol):
    dtype: pa.DataType
    null_count: int
    null_ratio: float
    distribution_drift_score: float | None
    suggested_rules: list[CleanseRule]
