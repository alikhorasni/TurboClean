"""
PureData: Ultra-fast, adaptive data purification engine.
"""

from .engine import DataPurityEngine
from .contracts import FileFormat, CleanseRule, DataProfile, ColumnProfile
from .profiling import DynamicProfiler
from .cleaners import (
    MissingCleaner,
    OutlierCleaner,
    DriftCorrector,
    Normalizer,
    CategoryCleaner,
    DateFormatter,
    Deduplicator,
    TextNormalizer,
    TypeCaster,
)
from .reporting import ReportGenerator
from .rule_factory import rule_factory

__version__ = "0.3.0"
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
