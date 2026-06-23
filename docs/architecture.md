# Architecture

TurboClean follows a layered, strategy‑based architecture.

## Layers

1. **IO Layer** (`io_adapter`) – Lazy scans and memory‑mapped reads, returning `polars.LazyFrame`.
2. **Profiling Layer** (`profiling`) – Single‑pass statistical profiling with distribution drift detection.
3. **Cleansing Layer** (`cleaners`) – A collection of `CleanseRule` objects, each implementing `apply`.
4. **Reporting Layer** (`reporting`) – Generates Markdown/JSON reports.

All operations are lazy until `collect()` or `write()` is called, allowing Polars’ query optimizer to fuse, push down predicates, and minimise memory usage.

## Zero‑Copy Data Exchange

Because Polars and PyArrow share the same Arrow memory layout, converting between formats (e.g., Parquet → CSV) happens without copying data buffers – we simply pass Arrow tables or batches directly.
