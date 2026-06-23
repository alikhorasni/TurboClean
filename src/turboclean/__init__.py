"""
TurboClean: Ultra-fast, adaptive data cleansing engine.
"""

from .cleaners import (
    CategoryCleaner,
    DateFormatter,
    Deduplicator,
    DriftCorrector,
    MissingCleaner,
    Normalizer,
    OutlierCleaner,
    TextNormalizer,
    TypeCaster,
)
from .contracts import CleanseRule, ColumnProfile, DataProfile, FileFormat
from .engine import DataPurityEngine
from .profiling import DynamicProfiler
from .reporting import ReportGenerator
from .rule_factory import rule_factory

__version__ = "0.3.1"
__all__ = [
    "DataPurityEngine",
    "DynamicProfiler",
    "MissingCleaner",
    "OutlierCleaner",
    "DriftCorrector",
    "Normalizer",
    "CategoryCleaner",
    "DateFormatter",
    "Deduplicator",
    "TextNormalizer",
    "TypeCaster",
    "ReportGenerator",
    "rule_factory",
    "FileFormat",
    "CleanseRule",
    "DataProfile",
    "ColumnProfile",
]
