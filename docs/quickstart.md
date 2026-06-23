# Quickstart

Install PureData:
```bash
pip install puredata
```
1‑Line Magic
```python
from pure_data import DataPurityEngine
DataPurityEngine().load("dirty.csv").suggest_cleansing_rules().clean().write("clean.parquet")
```
CLI
```bash
puredata clean dirty.csv clean.parquet --auto-magic
puredata profile dirty.csv --report report.md
```
Custom Cleaning Rules (YAML)
```yaml
- type: missing
  column: age
  strategy: median
- type: outlier
  column: salary
  method: iqr
```
```bash
puredata clean dirty.csv clean.parquet --config rules.yaml
```
