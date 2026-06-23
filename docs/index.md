# PureData Documentation

**Ultra‑fast, adaptive data cleansing at scale.**

PureData is a Python library that profiles, validates, and cleans massive datasets without loading them entirely into memory. It uses lazy evaluation via Polars and zero‑copy data sharing through Apache Arrow, making it 5 × faster than Pandas on files up to hundreds of gigabytes.

## Key Features

- **Auto‑magic cleaning** – one line to clean a messy dataset completely.
- **Dynamic distribution drift detection** – finds hidden shifts in your data over time.
- **Lazy & streaming execution** – works on data too large for RAM.
- **Extensible strategy pattern** – write a custom `Cleaner` in seconds.
- **Rich CLI** – beautiful, intuitive interface with progress bars.
- **Multi‑format support** – CSV, JSON, Parquet, Excel, SQL, and more.
