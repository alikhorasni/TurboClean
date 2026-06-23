from __future__ import annotations
from typing import Any
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
from .contracts import CleanseRule

_RULE_MAP: dict[str, type[CleanseRule]] = {
    "missing": MissingCleaner,
    "outlier": OutlierCleaner,
    "drift": DriftCorrector,
    "normalize": Normalizer,
    "category": CategoryCleaner,
    "date_format": DateFormatter,
    "deduplicate": Deduplicator,
    "text_normalize": TextNormalizer,
    "type_cast": TypeCaster,
}

def rule_factory(config: list[dict[str, Any]]) -> list[CleanseRule]:
    """Convert a list of configuration dictionaries into cleansing rules."""
    rules: list[CleanseRule] = []
    for entry in config:
        rule_type = entry.pop("type")
        cls = _RULE_MAP.get(rule_type)
        if cls is None:
            raise ValueError(f"Unknown rule type: {rule_type}")
        rules.append(cls(**entry))
    return rules
