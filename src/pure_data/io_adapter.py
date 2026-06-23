from __future__ import annotations
import mmap
from pathlib import Path
from typing import Any
import polars as pl
import pyarrow.parquet as pq
from .contracts import Connector, FileFormat

class IOAdapter:
    """Optimised I/O adapter with lazy scanning and row count estimation."""

    @staticmethod
    def read_lazyframe(
        source: str | Path | Connector,
        fmt: FileFormat | None = None,
        **kwargs: Any,
    ) -> pl.LazyFrame:
        if isinstance(source, Connector):
            return IOAdapter._read_sql(source, **kwargs)
        path = Path(source)
        fmt = fmt or IOAdapter._detect_format(path)

        if fmt == FileFormat.PARQUET:
            return pl.scan_parquet(path, **kwargs)
        elif fmt == FileFormat.CSV:
            return pl.scan_csv(path, **kwargs)
        elif fmt == FileFormat.JSON:
            return pl.scan_ndjson(path, **kwargs)
        else:
            # Fallback for formats without native lazy scan
            return IOAdapter._read_eager(path, fmt).lazy()

    @staticmethod
    def estimate_row_count(
        source: str | Path | Connector, fmt: FileFormat | None = None
    ) -> int:
        """Estimate row count without full scan (best effort)."""
        if isinstance(source, Connector):
            return 0  # not implemented for SQL yet
        path = Path(source)
        fmt = fmt or IOAdapter._detect_format(path)
        if fmt == FileFormat.PARQUET:
            with path.open("rb") as f:
                return pq.ParquetFile(f).metadata.num_rows
        elif fmt == FileFormat.CSV:
            with path.open("rb") as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                try:
                    return mm[:].count(b"\n")
                finally:
                    mm.close()
        return 0

    @staticmethod
    def _detect_format(path: Path) -> FileFormat:
        ext = path.suffix.lower()
        return {
            ".csv": FileFormat.CSV,
            ".tsv": FileFormat.CSV,
            ".json": FileFormat.JSON,
            ".parquet": FileFormat.PARQUET,
            ".avro": FileFormat.AVRO,
            ".xlsx": FileFormat.EXCEL,
            ".xml": FileFormat.XML,
        }.get(ext, FileFormat.CSV)

    @staticmethod
    def _read_eager(path: Path, fmt: FileFormat) -> pl.DataFrame:
        if fmt == FileFormat.EXCEL:
            import pandas as pd
            return pl.from_pandas(pd.read_excel(path))
        # Other formats will be added incrementally
        raise NotImplementedError(f"Eager reader for {fmt} not yet implemented")

    @staticmethod
    def _read_sql(connector: Connector, **kwargs: Any) -> pl.LazyFrame:
        import pandas as pd
        query = kwargs.get("query", "SELECT * FROM table")
        engine = connector  # assumed to be SQLAlchemy engine
        pdf = pd.read_sql(query, engine)
        return pl.from_pandas(pdf).lazy()
