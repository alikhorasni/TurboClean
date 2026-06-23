from pathlib import Path
import polars as pl
import pytest
from pure_data.io_adapter import IOAdapter

class TestReadLazyFrame:
    def test_read_csv(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "test.csv"
        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        df.write_csv(csv_file)
        lf = IOAdapter.read_lazyframe(csv_file)
        assert lf.columns == ["a", "b"]
        assert lf.collect().shape == (2, 2)

    def test_read_parquet(self, tmp_path: Path) -> None:
        parquet_file = tmp_path / "test.parquet"
        df = pl.DataFrame({"x": [1.0, 2.0]})
        df.write_parquet(parquet_file)
        lf = IOAdapter.read_lazyframe(parquet_file)
        assert lf.columns == ["x"]
        assert lf.collect().shape == (2, 1)

    def test_read_ndjson(self, tmp_path: Path) -> None:
        json_file = tmp_path / "test.json"
        df = pl.DataFrame({"col": [1, 2]})
        df.write_ndjson(json_file)
        lf = IOAdapter.read_lazyframe(json_file)
        assert lf.columns == ["col"]
        assert lf.collect().shape == (2, 1)

    def test_format_detection(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a\n1\n")
        lf = IOAdapter.read_lazyframe(csv_file)
        assert lf.collect().height == 1

    def test_eager_fallback_excel(self, tmp_path: Path) -> None:
        pytest.importorskip("openpyxl")
        excel_file = tmp_path / "test.xlsx"
        import pandas as pd
        pd.DataFrame({"num": [1, 2]}).to_excel(excel_file, index=False)
        lf = IOAdapter.read_lazyframe(excel_file)
        assert lf.collect().shape == (2, 1)

class TestEstimateRowCount:
    def test_parquet_row_count(self, tmp_path: Path) -> None:
        parquet_file = tmp_path / "test.parquet"
        pl.DataFrame({"a": range(100)}).write_parquet(parquet_file)
        count = IOAdapter.estimate_row_count(parquet_file)
        assert count == 100

    def test_csv_row_count(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("col1\n1\n2\n3\n")
        count = IOAdapter.estimate_row_count(csv_file)
        assert count == 3
