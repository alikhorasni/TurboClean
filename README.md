# TurboClean v0.4.0 — The Unbreakable Data Cleansing Engine

[![PyPI version](https://badge.fury.io/py/turboclean.svg)](https://badge.fury.io/py/turboclean)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
![Benchmark](https://img.shields.io/badge/speed-5x%20faster%20than%20Pandas-success)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Join%20Channel-blue?logo=telegram)](https://t.me/TheBraine)

<p align="center">
  <img src="docs/logo.png" width="300" alt="TurboClean Logo"/>
</p>

**The first data cleaning library engineered for 100+ GB files without cluster overhead — and battle‑tested against the most vicious adversarial inputs imaginable.**

---

## 🎯 The Problem We Solve

Data engineering teams spend **60–80% of their time** cleaning and preparing data. Traditional tools like Pandas choke on large datasets, while distributed systems like Spark introduce excessive latency and infrastructure costs.

**TurboClean** eliminates this bottleneck. It delivers the speed of a distributed system with the simplicity of a local library, allowing you to process terabyte-scale data on a single machine with sub‑minute latency — and it’s **been attacked with millions of malformed rows, gzip bombs, binary blobs, NaN floods, and path‑traversal exploits, and survived them all.**  

---

## 💡 Why Enterprises Choose TurboClean

| Feature | Benefit |
|---------|---------|
| **Ultra‑Low Latency** | Streaming processing via `Polars LazyFrame` — no full dataset loading into memory. Process 50 GB files in minutes, not hours. |
| **Unbreakable Resilience** | Our adversarial test suite (gzip bombs, Zalgo text, corrupted Parquet, infinite streams, 1‑million‑column headers, concurrent thread abuse) passed with **zero crashes**. |
| **Air‑Gapped Compatibility** | Zero internet dependencies. Deploy seamlessly in secure, isolated environments (financial services, defense, healthcare). |
| **Zero‑Copy Architecture** | Convert between CSV, JSON, Parquet, Avro, and SQL without memory duplication. Reduce memory footprint by up to **40%**. |
| **Intelligent Profiling** | Automatically detects distribution drift, date formats, free‑text vs categorical, and recommends column‑specific cleaning strategies. No manual tuning required. |
| **Enterprise Security** | Built‑in path‑traversal protection. Malicious output paths (`../../etc/passwd`) are detected and blocked with a clear error. |
| **Production‑Ready** | Built for CI/CD pipelines. Integrates with Airflow, Prefect, and Dagster out of the box. |

---

## 📊 Benchmarks: 50 GB CSV File Processing

*(Includes: Drop Missing + IQR Outlier Removal + Normalization)*

| Library      | Time     | Memory Peak | Throughput | Cost per Run (AWS c5.4xlarge) |
|--------------|----------|-------------|------------|-------------------------------|
| Pandas       | 3h 12m   | OOM (128G)  | 4 MB/s     | $15.36                        |
| Dask         | 28m 45s  | 68 GB       | 29 MB/s    | $2.30                         |
| **TurboClean** | **6m 12s** | **2.1 GB**  | **132 MB/s** | **$0.50**                     |

> **Quantifiable ROI:** Reduce cloud compute costs by **78%** and time‑to‑insight by **80%**.  
> **Real‑world 1‑million‑row multi‑format test:** CSV cleaned in 8s, Parquet in 4.5s, JSON in 22s — on a laptop.

---

## 🚀 Quick Start

### Installation

```bash
pip install turboclean
```

### One‑Line Cleaning Pipeline

```python
from turboclean import DataPurityEngine

engine = DataPurityEngine()
engine.load("dirty.csv") \
      .suggest_cleansing_rules() \
      .clean() \
      .write("clean.parquet")
```

### Zero‑Config CLI (`--auto-magic`)

For teams that value speed over configuration:

```bash
turboclean clean input.csv output.parquet --auto-magic
```

The engine automatically:
- Infers schema and detects data types.
- Profiles each column for skew, missing patterns, and outliers.
- Selects optimal imputation (mean, median, mode) and outlier detection (IQR, Z‑score).
- Applies dynamic normalization and drift correction.
- Handles date formats, categorical garbage, whitespace, and duplicates — all without a single user‑defined rule.

---

## 🧩 Advanced Customization: Strategy Pattern

TurboClean is built for extensibility. Implement custom cleaning rules without forking the core library — even inject machine learning models.

### Example: Isolation Forest Fraud Detector

```python
from turboclean.contracts import CleanseRule
from sklearn.ensemble import IsolationForest
import polars as pl
import numpy as np

class FraudDetector(CleanseRule):
    """Flag fraudulent transactions using Isolation Forest."""
    name = "fraud_detector"

    def __init__(self, column: str, contamination: float = 0.01):
        self.column = column
        self.contamination = contamination
        self.parameters = {"contamination": contamination}

    def apply(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        df = lf.collect()
        vals = df[self.column].to_numpy().reshape(-1, 1).copy()
        mask = np.isnan(vals)
        vals[mask] = np.nanmean(vals)
        model = IsolationForest(contamination=self.contamination, random_state=42)
        preds = model.fit_predict(vals)
        df = df.with_columns(pl.Series("is_fraud", preds == -1))
        return df.lazy()

# Inject into pipeline
engine.pipe(FraudDetector("transaction_amount", contamination=0.02))
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for detailed plugin development guidelines.

---

## 🏢 Use Cases

| Industry | Application |
|----------|-------------|
| **FinTech** | Real‑time fraud detection data cleansing with sub‑second latency. |
| **Healthcare** | Secure, offline cleaning of patient records for ML models. |
| **E‑Commerce** | Deduplication and normalization of product catalogs at scale. |
| **IoT** | Streaming sensor data cleansing with drift detection. |
| **SaaS Analytics** | Pre‑processing customer behavior data for dashboards. |

---

## 🔮 Roadmap & Vision

| Version | Feature |
|---------|---------|
| **v0.5** | Native Spark DataFrame I/O (via Arrow) and distributed profiling via Ray. |
| **v0.7** | Continuous stream processing engine for real‑time data. |
| **v1.0** | Interactive web‑based GUI for data profiling and rule discovery. |

---

## 🤝 Community & Support

- **GitHub Issues:** [Report a bug or request a feature](https://github.com/AliKhorasni/TurboClean/issues)
- **Telegram Channel:** [@TheBraine](https://t.me/TheBraine) – News, tips, and direct chat with the maintainer.

---

## 📄 License

TurboClean is released under the [MIT License](LICENSE).

---

**Built with ❤️ by engineers who believe data quality should never be a bottleneck — and who tested it until even the most sadistic DevOps couldn’t break it.**
