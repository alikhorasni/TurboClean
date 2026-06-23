from __future__ import annotations
from pathlib import Path
from typing import Any, TypeVar
import pyarrow as pa
import polars as pl
from .contracts import CleanseRule, Connector, DataProfile, FileFormat
from .exceptions import EmptyDatasetError
from .io_adapter import IOAdapter
from .utils import benchmark

Self = TypeVar("Self", bound="DataPurityEngine")

class DataPurityEngine:
    """Core engine for intelligent data screening, cleaning, and quality improvement."""

    def __init__(self) -> None:
        self._lf: pl.LazyFrame | None = None
        self._schema: pa.Schema | None = None
        self._profile: DataProfile | None = None
        self._rules: list[CleanseRule] = []

    @benchmark
    def load(
        self,
        source: str | Path | Connector,
        format: FileFormat | None = None,
        lazy: bool = True,
        **kwargs: Any,
    ) -> Self:
        if not lazy:
            raise ValueError("PureData core only supports lazy=True")
        self._lf = IOAdapter.read_lazyframe(source, format, **kwargs)
        if not self._lf.columns:
            raise EmptyDatasetError("The dataset has no columns.")
        return self

    @benchmark
    def infer_schema(self, sample_size: int = 10_000) -> pa.Schema:
        if self._lf is None:
            raise RuntimeError("No data loaded. Call load() first.")
        sample = self._lf.fetch(sample_size)
        self._schema = sample.to_arrow().schema
        return self._schema

    @benchmark
    def suggest_cleansing_rules(self) -> list[CleanseRule]:
        if self._lf is None:
            raise RuntimeError("No data loaded. Call load() first.")
        from .profiling import DynamicProfiler
        profiler = DynamicProfiler(self._lf)
        self._profile = profiler.generate_profile()
        rules: list[CleanseRule] = []
        for cprof in self._profile.column_profiles.values():
            rules.extend(cprof.suggested_rules)
        self._rules = rules
        return rules

    @benchmark
    def apply_profile(self, profile: DataProfile, in_place: bool = False) -> Self:
        self._profile = profile
        return self

    @benchmark
    def clean(self, rules: list[CleanseRule] | None = None) -> Self:
        if self._lf is None:
            raise RuntimeError("No data loaded. Call load() first.")
        apply_rules = rules or self._rules
        for rule in apply_rules:
            self._lf = rule.apply(self._lf)
        return self

    def pipe(self, rule: CleanseRule) -> Self:
        """Apply a single cleansing rule and return self for method chaining."""
        if self._lf is None:
            raise RuntimeError("No data loaded. Call load() first.")
        self._lf = rule.apply(self._lf)
        return self

    def collect(self) -> pl.DataFrame:
        if self._lf is None:
            raise RuntimeError("No data loaded. Call load() first.")
        return self._lf.collect()

    def write(self, destination: str | Path, format: FileFormat) -> None:
        df = self._lf.collect() if self._lf is not None else pl.DataFrame()
        dest = Path(destination)
        if format == FileFormat.PARQUET:
            df.to_parquet(dest)
        elif format == FileFormat.CSV:
            df.to_csv(dest)
        elif format == FileFormat.JSON:
            df.to_ndjson(dest)
        else:
            raise ValueError(f"Unsupported output format: {format}")
