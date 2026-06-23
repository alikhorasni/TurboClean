from __future__ import annotations
from typing import Any, Dict, List
from .contracts import CleanseRule
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

_RULE_MAP = {
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


def rule_factory(config: List[Dict[str, Any]]) -> List[CleanseRule]:
    """Convert a list of configuration dictionaries into cleansing rules."""
    rules: List[CleanseRule] = []
    for entry in config:
        rule_type = entry.pop("type")
        cls = _RULE_MAP.get(rule_type)
        if cls is None:
            raise ValueError(f"Unknown rule type: {rule_type}")
        rules.append(cls(**entry))
    return rules
