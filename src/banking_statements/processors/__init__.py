"""
src/banking_statements/processors/__init__.py

Public processor contracts, registry, and default composition.
"""

from __future__ import annotations

from .base import ProcessorMatch, StatementProcessor
from .defaults import (
    build_default_institution_detector,
    build_default_processor_registry,
)
from .registry import ProcessorRegistry

__all__ = [
    "ProcessorMatch",
    "ProcessorRegistry",
    "StatementProcessor",
    "build_default_institution_detector",
    "build_default_processor_registry",
]
