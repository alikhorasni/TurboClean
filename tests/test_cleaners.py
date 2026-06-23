import polars as pl
from pure_data.cleaners import Deduplicator, MissingCleaner, OutlierCleaner

def test_missing_drop():
    lf = pl.LazyFrame({"a": [1, None, 3]})
    cleaner = MissingCleaner("a", "drop")
    result = cleaner.apply(lf).collect()
    assert result["a"].null_count() == 0
    assert result.shape[0] == 2

def test_outlier_iqr():
    lf = pl.LazyFrame({"x": [1, 2, 3, 100]})
    cleaner = OutlierCleaner("x", method="iqr")
    result = cleaner.apply(lf).collect()
    assert result["x"].max() <= 100

def test_deduplicate():
    lf = pl.LazyFrame({"id": [1, 2, 2]})
    dedup = Deduplicator(subset=["id"])
    result = dedup.apply(lf).collect()
    assert result.shape[0] == 2
