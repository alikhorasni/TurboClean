from __future__ import annotations

from typing import Any

import polars as pl

from .contracts import CleanseRule


class MissingCleaner(CleanseRule):
    name = "missing_cleaner"

    def __init__(self, column: str, strategy: str = "drop") -> None:
        self.column = column
        self.strategy = strategy
        self.parameters: dict[str, Any] = {"column": column, "strategy": strategy}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        if self.strategy == "drop":
            return lf.filter(pl.col(self.column).is_not_null())
        elif self.strategy == "mean":
            mean_val = lf.select(pl.col(self.column).mean()).collect().item()
            return lf.with_columns(pl.col(self.column).fill_null(mean_val))
        elif self.strategy == "median":
            median_val = lf.select(pl.col(self.column).median()).collect().item()
            return lf.with_columns(pl.col(self.column).fill_null(median_val))
        elif self.strategy == "mode":
            mode_val = lf.select(pl.col(self.column).mode().first()).collect().item()
            return lf.with_columns(pl.col(self.column).fill_null(mode_val))
        elif self.strategy == "forward_fill":
            return lf.with_columns(pl.col(self.column).forward_fill())
        elif self.strategy == "backward_fill":
            return lf.with_columns(pl.col(self.column).backward_fill())
        else:
            raise ValueError(f"Unknown missing strategy: {self.strategy}")

class OutlierCleaner(CleanseRule):
    name = "outlier_cleaner"

    def __init__(self, column: str, method: str = "iqr", factor: float = 1.5) -> None:
        self.column = column
        self.method = method
        self.factor = factor
        self.parameters = {"column": column, "method": method, "factor": factor}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        if self.method == "iqr":
            q1 = lf.select(pl.col(self.column).quantile(0.25)).collect().item()
            q3 = lf.select(pl.col(self.column).quantile(0.75)).collect().item()
            iqr = q3 - q1
            lower = q1 - self.factor * iqr
            upper = q3 + self.factor * iqr
            return lf.with_columns(
                pl.when(pl.col(self.column) < lower)
                .then(lower)
                .when(pl.col(self.column) > upper)
                .then(upper)
                .otherwise(pl.col(self.column))
                .alias(self.column)
            )
        elif self.method == "zscore":
            mean = lf.select(pl.col(self.column).mean()).collect().item()
            std = lf.select(pl.col(self.column).std()).collect().item()
            threshold = self.factor
            return lf.with_columns(
                pl.when((pl.col(self.column) - mean).abs() > threshold * std)
                .then(mean)
                .otherwise(pl.col(self.column))
                .alias(self.column)
            )
        else:
            raise ValueError(f"Unknown outlier method: {self.method}")

class DriftCorrector(CleanseRule):
    name = "drift_corrector"

    def __init__(self, column: str) -> None:
        self.column = column
        self.parameters = {"column": column}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        q_low = lf.select(pl.col(self.column).quantile(0.05)).collect().item()
        q_high = lf.select(pl.col(self.column).quantile(0.95)).collect().item()
        return lf.with_columns(
            pl.when(pl.col(self.column) < q_low)
            .then(q_low)
            .when(pl.col(self.column) > q_high)
            .then(q_high)
            .otherwise(pl.col(self.column))
            .alias(self.column)
        )

class Normalizer(CleanseRule):
    name = "normalizer"

    def __init__(self, column: str, method: str = "zscore") -> None:
        self.column = column
        self.method = method
        self.parameters = {"column": column, "method": method}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        if self.method == "zscore":
            mean = lf.select(pl.col(self.column).mean()).collect().item()
            std = lf.select(pl.col(self.column).std()).collect().item()
            return lf.with_columns(
                ((pl.col(self.column) - mean) / std).alias(self.column)
            )
        elif self.method == "minmax":
            min_val = lf.select(pl.col(self.column).min()).collect().item()
            max_val = lf.select(pl.col(self.column).max()).collect().item()
            return lf.with_columns(
                ((pl.col(self.column) - min_val) / (max_val - min_val)).alias(self.column)
            )
        else:
            raise ValueError(f"Unknown normalization method: {self.method}")

class CategoryCleaner(CleanseRule):
    name = "category_cleaner"

    def __init__(self, column: str, max_categories: int = 50, rare_threshold: float = 0.01) -> None:
        self.column = column
        self.max_categories = max_categories
        self.rare_threshold = rare_threshold
        self.parameters = {
            "column": column,
            "max_categories": max_categories,
            "rare_threshold": rare_threshold,
        }

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        lf = lf.with_columns(
                        (pl.col(self.column)).str.strip_chars().str.to_lowercase().alias(self.column)
        )
        freq = lf.group_by(self.column).agg(pl.count().alias("__cnt")).collect()
        total = freq["__cnt"].sum()
        freq = freq.with_columns((pl.col("__cnt") / total).alias("__freq"))
        rare_vals = set(
            freq.filter(pl.col("__freq") < self.rare_threshold)[self.column].to_list()
        )
        if rare_vals:
            lf = lf.with_columns(
                pl.when(pl.col(self.column).is_in(rare_vals))
                .then(pl.lit("other"))
                .otherwise(pl.col(self.column))
                .alias(self.column)
            )
        return lf

class DateFormatter(CleanseRule):
    name = "date_formatter"

    def __init__(self, column: str, target_format: str = "%Y-%m-%d") -> None:
        self.column = column
        self.target_format = target_format
        self.parameters = {"column": column, "target_format": target_format}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.with_columns(
            pl.col(self.column)
            .str.strptime(pl.Date, strict=False)
            .dt.strftime(self.target_format)
            .alias(self.column)
        )

class Deduplicator(CleanseRule):
    name = "deduplicator"

    def __init__(self, subset: list[str] | None = None) -> None:
        self.column = "__all__"
        self.subset = subset
        self.parameters = {"subset": subset}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.unique(subset=self.subset)

class TextNormalizer(CleanseRule):
    name = "text_normalizer"

    def __init__(self, column: str, lower: bool = True, trim: bool = True) -> None:
        self.column = column
        self.lower = lower
        self.trim = trim
        self.parameters = {"column": column, "lower": lower, "trim": trim}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        expr = pl.col(self.column)
        if self.trim:
            expr = expr.str.strip_chars()
        if self.lower:
            expr = expr.str.to_lowercase()
        return lf.with_columns(expr.alias(self.column))

class TypeCaster(CleanseRule):
    name = "type_caster"

    def __init__(self, column: str, target_type: Any) -> None:
        self.column = column
        self.target_type = target_type
        self.parameters = {"column": column, "target_type": str(target_type)}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.with_columns(pl.col(self.column).cast(self.target_type))
