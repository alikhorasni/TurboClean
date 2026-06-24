"""
Manually combining built‑in cleaners.

Shows how to select specific rules instead of using auto‑magic.
"""
from turboclean import DataPurityEngine
from turboclean.cleaners import MissingCleaner, OutlierCleaner, CategoryCleaner

engine = DataPurityEngine()
engine.load("example_dirty.csv")   # from example 01

# Build exactly the rules you need
rules = [
    MissingCleaner("age", strategy="median"),
    OutlierCleaner("age", method="iqr"),
    MissingCleaner("salary", strategy="mean"),
    CategoryCleaner("name"),
]

engine.clean(rules)
engine.write("example_custom_clean.csv")
print("✅ Cleaned with custom rules")
