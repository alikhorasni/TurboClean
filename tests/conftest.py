from datetime import datetime, timedelta

import numpy as np
import polars as pl
import pytest

from turboclean.engine import DataPurityEngine


@pytest.fixture(scope="module")
def large_dirty_df() -> pl.DataFrame:
    np.random.seed(42)
    n = 500_000
    base = datetime(2020, 1, 1)
    timestamps = [base + timedelta(minutes=i) for i in range(n)]
    values = np.concatenate([
        np.random.normal(100, 15, n // 2),
        np.random.normal(150, 20, n // 2),
    ])
    categories = np.random.choice(["A", "B", "C", None], n, p=[0.3, 0.3, 0.2, 0.2])
    return pl.DataFrame({
        "id": range(n),
        "value": values.tolist(),
        "category": categories.tolist(),
        "timestamp": timestamps,
        "text": ["  hello  " for _ in range(n)],
    })

@pytest.fixture
def engine() -> DataPurityEngine:
    return DataPurityEngine()
