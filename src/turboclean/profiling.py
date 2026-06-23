from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

import polars as pl
import pyarrow as pa

from .contracts import CleanseRule, ColumnProfile, DataProfile
from .utils import benchmark


@dataclass
class ConcreteColumnProfile(ColumnProfile):
    name: str
    dtype: pa.DataType
    null_count: int = 0
    null_ratio: float = 0.0
    distribution_drift_score: float | None = None
    suggested_rules: list[CleanseRule] = field(default_factory=list)
    basic_stats: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        drift = (
            f"Drift Score: {self.distribution_drift_score:.3f}"
            if self.distribution_drift_score is not None
            else "No drift"
        )
        return f"{self.name} ({self.dtype}): {self.null_count} nulls ({self.null_ratio:.1%}), {drift}"


@dataclass
class ConcreteDataProfile(DataProfile):
    schema: pa.Schema
    column_profiles: dict[str, ConcreteColumnProfile] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [f"Schema: {self.schema}"]
        for prof in self.column_profiles.values():
            lines.append(prof.summary())
        return "\n".join(lines)


class DynamicProfiler:
    """Statistical profiler with automatic distribution drift and date detection."""

    DATE_PATTERNS = [
        re.compile(r"(\d{4}[/-]\d{2}[/-]\d{2})"),
        re.compile(r"(\d{2}[/-]\d{2}[/-]\d{4})"),
        re.compile(r"(\d{2}\.\d{2}\.\d{4})"),
        re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})"),
    ]

    def __init__(self, lf: pl.LazyFrame) -> None:
        self._lf = lf

    @benchmark
    def generate_profile(self) -> ConcreteDataProfile:
        sample = self._lf.limit(1).collect()
        schema = sample.to_arrow().schema
        columns = self._lf.collect_schema().names()
        n_rows = self._lf.select(pl.len()).collect().item()

        aggs = []
        for col in columns:
            dtype = schema.field(col).type
            aggs.append(pl.col(col).null_count().alias(f"__nullcnt_{col}"))
            if pa.types.is_integer(dtype) or pa.types.is_floating(dtype):
                aggs.extend([
                    pl.col(col).mean().alias(f"__mean_{col}"),
                    pl.col(col).std().alias(f"__std_{col}"),
                    pl.col(col).skew().alias(f"__skew_{col}"),
                    pl.col(col).kurtosis().alias(f"__kurt_{col}"),
                    pl.col(col).quantile(0.25).alias(f"__q25_{col}"),
                    pl.col(col).quantile(0.75).alias(f"__q75_{col}"),
                ])
        stats_df = self._lf.select(aggs).collect()
        stats_dict = stats_df.to_dicts()[0]

        drift_scores = self._compute_drift_scores(columns, schema, n_rows)

        duplicate_count = self._lf.collect().shape[0] - self._lf.unique().collect().shape[0]
        has_duplicates = duplicate_count > 0

        from .cleaners import (
            MissingCleaner,
            OutlierCleaner,
            DriftCorrector,
            CategoryCleaner,
            DateFormatter,
            TextNormalizer,
            Deduplicator,
            TypeCaster,
        )

        profiles: dict[str, ConcreteColumnProfile] = {}
        for col in columns:
            dtype = schema.field(col).type
            null_count = stats_dict.get(f"__nullcnt_{col}", 0)
            null_ratio = null_count / n_rows if n_rows else 0.0
            basic_stats: dict[str, Any] = {}
            drift_score = drift_scores.get(col)
            suggested_rules: list[CleanseRule] = []

            # Missing values
            if null_ratio > 0.0:
                if pa.types.is_string(dtype) or pa.types.is_large_string(dtype):
                    if self._looks_like_date(col, schema):
                        suggested_rules.append(MissingCleaner(column=col, strategy="drop"))
                    elif not self._is_free_text(col):
                        suggested_rules.append(MissingCleaner(column=col, strategy="fill", fill_value="unknown"))
                else:
                    suggested_rules.append(MissingCleaner(column=col, strategy="mean"))

            # Numeric columns
            if pa.types.is_integer(dtype) or pa.types.is_floating(dtype):
                basic_stats = {
                    "mean": stats_dict.get(f"__mean_{col}"),
                    "std": stats_dict.get(f"__std_{col}"),
                    "skew": stats_dict.get(f"__skew_{col}"),
                    "kurt": stats_dict.get(f"__kurt_{col}"),
                    "q25": stats_dict.get(f"__q25_{col}"),
                    "q75": stats_dict.get(f"__q75_{col}"),
                }
                if abs(basic_stats.get("skew", 0)) > 1.0 or abs(basic_stats.get("kurt", 0)) > 3.0:
                    suggested_rules.append(OutlierCleaner(column=col, method="iqr"))
                if drift_score is not None and drift_score > 0.1:
                    suggested_rules.append(DriftCorrector(column=col))
                if pa.types.is_integer(dtype):
                    suggested_rules.append(TypeCaster(column=col, target_type=pl.Int64))

            # String columns
            if pa.types.is_string(dtype) or pa.types.is_large_string(dtype):
                is_free_text = self._is_free_text(col)
                if is_free_text:
                    suggested_rules.append(TextNormalizer(column=col))
                else:
                    distinct = self._lf.select(pl.col(col).n_unique()).collect().item()
                    if distinct < 30:
                        suggested_rules.append(CategoryCleaner(column=col))
                    else:
                        suggested_rules.append(TextNormalizer(column=col))

                if self._looks_like_date(col, schema):
                    suggested_rules.append(DateFormatter(column=col))
                    if null_ratio > 0.0:
                        suggested_rules.append(MissingCleaner(column=col, strategy="drop"))

            profiles[col] = ConcreteColumnProfile(
                name=col,
                dtype=dtype,
                null_count=null_count,
                null_ratio=null_ratio,
                distribution_drift_score=drift_score,
                suggested_rules=suggested_rules,
                basic_stats=basic_stats,
            )

        if has_duplicates:
            first_col = columns[0] if columns else None
            if first_col:
                profiles[first_col].suggested_rules.append(Deduplicator())

        return ConcreteDataProfile(schema=schema, column_profiles=profiles)

    def _is_free_text(self, col: str) -> bool:
        return any(
            word in col.lower()
            for word in ("note", "text", "comment", "desc", "description", "message")
        )

    def _looks_like_date(self, col: str, schema: pa.Schema) -> bool:
        name_lower = col.lower()
        if any(word in name_lower for word in ("date", "time", "timestamp", "dt")):
            return True
        try:
            sample_vals = self._lf.select(pl.col(col).drop_nulls().limit(10)).collect().to_series().to_list()
            for val in sample_vals:
                if isinstance(val, str):
                    for pattern in self.DATE_PATTERNS:
                        if pattern.match(val.strip()):
                            return True
        except Exception:
            pass
        return False

    def _compute_drift_scores(
        self, columns: list[str], schema: pa.Schema, n_rows: int
    ) -> dict[str, float | None]:
        if n_rows < 2:
            return {col: None for col in columns}

        half = n_rows // 2
        numeric_cols = [
            col for col in columns
            if pa.types.is_integer(schema.field(col).type)
            or pa.types.is_floating(schema.field(col).type)
        ]
        if not numeric_cols:
            return {col: None for col in columns}

        lf_early = self._lf.slice(0, half)
        lf_late = self._lf.slice(half, n_rows - half)

        early_expr = []
        late_expr = []
        for col in numeric_cols:
            early_expr.extend([
                pl.col(col).mean().alias(f"__early_mean_{col}"),
                pl.col(col).std().alias(f"__early_std_{col}"),
            ])
            late_expr.extend([
                pl.col(col).mean().alias(f"__late_mean_{col}"),
                pl.col(col).std().alias(f"__late_std_{col}"),
            ])

        early_stats = lf_early.select(early_expr).collect().to_dicts()[0]
        late_stats = lf_late.select(late_expr).collect().to_dicts()[0]

        drift_scores: dict[str, float | None] = {}
        for col in numeric_cols:
            early_mean = early_stats.get(f"__early_mean_{col}")
            early_std = early_stats.get(f"__early_std_{col}")
            late_mean = late_stats.get(f"__late_mean_{col}")
            late_std = late_stats.get(f"__late_std_{col}")
            if early_mean is not None and late_mean is not None:
                denom = (early_std or 0) + (late_std or 0)
                if denom > 0:
                    drift_scores[col] = abs(early_mean - late_mean) / denom
                else:
                    drift_scores[col] = 0.0
            else:
                drift_scores[col] = None

        for col in columns:
            if col not in drift_scores:
                drift_scores[col] = None

        return drift_scores
