from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
    """Statistical profiler with automatic distribution drift detection."""

    def __init__(self, lf: pl.LazyFrame) -> None:
        self._lf = lf

    @benchmark
    def generate_profile(self) -> ConcreteDataProfile:
        sample = self._lf.fetch(1)
        schema = sample.to_arrow().schema
        columns = self._lf.columns
        n_rows = self._lf.select(pl.len()).collect().item() 

        aggs = []
        for col in columns:
            dtype = schema.field(col).type
            aggs.append(pl.col(col).null_count().alias(f"__nullcnt_{col}"))
            if pa.types.is_numeric(dtype):
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

        profiles: dict[str, ConcreteColumnProfile] = {}
        for col in columns:
            dtype = schema.field(col).type
            null_count = stats_dict.get(f"__nullcnt_{col}", 0)
            null_ratio = null_count / n_rows if n_rows else 0.0
            basic_stats: dict[str, Any] = {}
            drift_score = drift_scores.get(col)
            suggested_rules: list[CleanseRule] = []

            if pa.types.is_numeric(dtype):
                basic_stats = {
                    "mean": stats_dict.get(f"__mean_{col}"),
                    "std": stats_dict.get(f"__std_{col}"),
                    "skew": stats_dict.get(f"__skew_{col}"),
                    "kurt": stats_dict.get(f"__kurt_{col}"),
                    "q25": stats_dict.get(f"__q25_{col}"),
                    "q75": stats_dict.get(f"__q75_{col}"),
                }
                from .cleaners import (
                    DriftCorrector,
                    MissingCleaner,
                    Normalizer,
                    OutlierCleaner,
                )
                if null_ratio > 0.05:
                    suggested_rules.append(MissingCleaner(column=col, strategy="mean"))
                if abs(basic_stats.get("skew", 0)) > 1.0 or abs(basic_stats.get("kurt", 0)) > 3.0:
                    suggested_rules.append(OutlierCleaner(column=col, method="iqr"))
                if drift_score is not None and drift_score > 0.1:
                    suggested_rules.append(DriftCorrector(column=col))
                if suggested_rules:
                    suggested_rules.append(Normalizer(column=col, method="zscore"))

            profiles[col] = ConcreteColumnProfile(
                name=col,
                dtype=dtype,
                null_count=null_count,
                null_ratio=null_ratio,
                distribution_drift_score=drift_score,
                suggested_rules=suggested_rules,
                basic_stats=basic_stats,
            )

        return ConcreteDataProfile(schema=schema, column_profiles=profiles)

    def _compute_drift_scores(
        self, columns: list[str], schema: pa.Schema, n_rows: int
    ) -> dict[str, float | None]:
        if n_rows < 2:
            return {col: None for col in columns}

        half = n_rows // 2
        numeric_cols = [col for col in columns if pa.types.is_numeric(schema.field(col).type)]
        if not numeric_cols:
            return {col: None for col in columns}

        early_expr = []
        late_expr = []
        for col in numeric_cols:
            early_expr.extend([
                pl.col(col).slice(0, half).mean().alias(f"__early_mean_{col}"),
                pl.col(col).slice(0, half).std().alias(f"__early_std_{col}"),
            ])
            late_expr.extend([
                pl.col(col).slice(half).mean().alias(f"__late_mean_{col}"),
                pl.col(col).slice(half).std().alias(f"__late_std_{col}"),
            ])
        stats = self._lf.select(early_expr + late_expr).collect().to_dicts()[0]

        drift_scores: dict[str, float | None] = {}
        for col in numeric_cols:
            early_mean = stats.get(f"__early_mean_{col}")
            early_std = stats.get(f"__early_std_{col}")
            late_mean = stats.get(f"__late_mean_{col}")
            late_std = stats.get(f"__late_std_{col}")
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
