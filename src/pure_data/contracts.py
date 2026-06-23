from __future__ import annotations
from typing import Protocol, TypeVar, List, Optional, Dict, Any
import enum
import pyarrow as pa
import polars

T = TypeVar("T", covariant=True)


class FileFormat(enum.Enum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    AVRO = "avro"
    EXCEL = "excel"
    XML = "xml"
    SQL = "sql"


class Connector(Protocol):
    """Protocol for SQLAlchemy-compatible database connections."""

    def execute(self, query: str) -> Any: ...
    @property
    def dialect(self) -> str: ...


class CleanseRule(Protocol):
    """Independent cleansing rule with an apply method."""

    name: str
    column: str
    parameters: Dict[str, Any]

    def apply(self, lf: polars.LazyFrame) -> polars.LazyFrame: ...


class DataProfile(Protocol):
    """Full statistical profile of a dataset."""

    schema: pa.Schema
    column_profiles: Dict[str, "ColumnProfile"]

    def summary(self) -> str: ...


class ColumnProfile(Protocol):
    dtype: pa.DataType
    null_count: int
    distribution_drift_score: Optional[float]
    suggested_rules: List[CleanseRule]
