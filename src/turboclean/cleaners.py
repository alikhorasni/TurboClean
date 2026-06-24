from __future__ import annotations

import re
from typing import Any

from .compat import pl
from .contracts import CleanseRule


class MissingCleaner(CleanseRule):
    name = "missing_cleaner"

    def __init__(self, column: str, strategy: str = "drop", fill_value: str = "unknown", numeric_fallback: float = 0.0) -> None:
        self.column = column
        self.strategy = strategy
        self.fill_value = fill_value
        self.numeric_fallback = numeric_fallback
        self.parameters: dict[str, Any] = {
            "column": column,
            "strategy": strategy,
            "fill_value": fill_value,
        }

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        col = pl.col(self.column)
        if self.strategy == "drop":
            return lf.filter(col.is_not_null())
        elif self.strategy == "mean":
            mean_val = lf.select(col.mean()).collect().item()
            if mean_val is None:
                mean_val = self.numeric_fallback
            return lf.with_columns(col.fill_null(mean_val))
        elif self.strategy == "median":
            median_val = lf.select(col.median()).collect().item()
            if median_val is None:
                median_val = self.numeric_fallback
            return lf.with_columns(col.fill_null(median_val))
        elif self.strategy == "mode":
            mode_val = lf.select(col.mode().first()).collect().item()
            if mode_val is None:
                mode_val = self.numeric_fallback
            return lf.with_columns(col.fill_null(mode_val))
        elif self.strategy == "fill":
            return lf.with_columns(col.fill_null(self.fill_value))
        elif self.strategy == "forward_fill":
            return lf.with_columns(col.forward_fill())
        elif self.strategy == "backward_fill":
            return lf.with_columns(col.backward_fill())
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
        col = pl.col(self.column)
        if self.method == "iqr":
            q1 = lf.select(col.quantile(0.25)).collect().item()
            q3 = lf.select(col.quantile(0.75)).collect().item()
            iqr = q3 - q1
            lower = q1 - self.factor * iqr
            upper = q3 + self.factor * iqr
            return lf.with_columns(
                pl.when(col < lower)
                .then(lower)
                .when(col > upper)
                .then(upper)
                .otherwise(col)
                .alias(self.column)
            )
        elif self.method == "zscore":
            mean = lf.select(col.mean()).collect().item()
            std = lf.select(col.std()).collect().item()
            if std is None or std == 0:
                return lf
            threshold = self.factor
            return lf.with_columns(
                pl.when((col - mean).abs() > threshold * std)
                .then(mean)
                .otherwise(col)
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
        col = pl.col(self.column)
        q_low = lf.select(col.quantile(0.05)).collect().item()
        q_high = lf.select(col.quantile(0.95)).collect().item()
        if q_low is None or q_high is None:
            return lf
        return lf.with_columns(
            pl.when(col < q_low)
            .then(q_low)
            .when(col > q_high)
            .then(q_high)
            .otherwise(col)
            .alias(self.column)
        )


class Normalizer(CleanseRule):
    name = "normalizer"

    def __init__(self, column: str, method: str = "zscore") -> None:
        self.column = column
        self.method = method
        self.parameters = {"column": column, "method": method}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        col = pl.col(self.column)
        if self.method == "zscore":
            mean = lf.select(col.mean()).collect().item()
            std = lf.select(col.std()).collect().item()
            if std is None or std == 0:
                return lf
            return lf.with_columns(((col - mean) / std).alias(self.column))
        elif self.method == "minmax":
            min_val = lf.select(col.min()).collect().item()
            max_val = lf.select(col.max()).collect().item()
            if min_val is None or max_val is None or max_val == min_val:
                return lf
            return lf.with_columns(((col - min_val) / (max_val - min_val)).alias(self.column))
        else:
            raise ValueError(f"Unknown normalization method: {self.method}")


class CategoryCleaner(CleanseRule):
    name = "category_cleaner"

    GARBAGE_PATTERN = re.compile(r"(non-existent|junk|test|dummy|delete|temp|xyz)", re.IGNORECASE)

    def __init__(self, column: str, max_categories: int = 50, rare_threshold: float = 0.0) -> None:
        self.column = column
        self.max_categories = max_categories
        self.rare_threshold = rare_threshold
        self.parameters = {
            "column": column,
            "max_categories": max_categories,
            "rare_threshold": rare_threshold,
        }

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        col = pl.col(self.column)
        lf = lf.with_columns(
            col.str.strip_chars().str.to_lowercase().alias(self.column)
        )

        freq = lf.group_by(self.column).agg(pl.len()).collect()
        all_vals = freq[self.column].to_list()

        to_remove: set[str] = set()
        for val in all_vals:
            if val is None:
                continue
            if not isinstance(val, str):
                continue
            if self.GARBAGE_PATTERN.search(val):
                to_remove.add(val)
            elif len(val) > 25 or (val.count("-") > 3):
                to_remove.add(val)

        if to_remove:
            lf = lf.with_columns(
                pl.when(col.is_in(to_remove))
                .then(pl.lit("other"))
                .otherwise(col)
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
        col = pl.col(self.column)
        return lf.with_columns(
            col.str.strptime(pl.Date, strict=False)
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

    def __init__(self, column: str, lower: bool = True, trim: bool = True, collapse_whitespace: bool = True) -> None:
        self.column = column
        self.lower = lower
        self.trim = trim
        self.collapse_whitespace = collapse_whitespace
        self.parameters = {
            "column": column,
            "lower": lower,
            "trim": trim,
            "collapse_whitespace": collapse_whitespace,
        }

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        expr = pl.col(self.column)
        if self.trim:
            expr = expr.str.strip_chars()
        if self.lower:
            expr = expr.str.to_lowercase()
        if self.collapse_whitespace:
            expr = expr.str.replace_all(r"\s+", " ")
        return lf.with_columns(expr.alias(self.column))


class TypeCaster(CleanseRule):
    name = "type_caster"

    def __init__(self, column: str, target_type: Any) -> None:
        self.column = column
        self.target_type = target_type
        self.parameters = {"column": column, "target_type": str(target_type)}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        return lf.with_columns(pl.col(self.column).cast(self.target_type))
