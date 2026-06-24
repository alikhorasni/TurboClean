"""
Loading from a URL (requires fsspec).
"""
import polars as pl
from turboclean import DataPurityEngine

# Directly load a publicly available CSV
url = "https://raw.githubusercontent.com/datasets/air-quality/master/data/air-quality.csv"

engine = DataPurityEngine()
engine.load(url) \
      .suggest_cleansing_rules() \
      .clean() \
      .write("air_quality_clean.parquet")
print("✅ URL data cleaned")
