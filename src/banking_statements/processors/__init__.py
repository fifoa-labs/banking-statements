"""
src/banking_statements/processors/__init__.py

Public processor contracts and registry.
"""

from __future__ import annotations

from .base import ProcessorMatch, StatementProcessor
from .registry import ProcessorRegistry

__all__ = [
    "ProcessorMatch",
    "ProcessorRegistry",
    "StatementProcessor",
]
