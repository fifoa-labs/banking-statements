"""
src/banking_statements/processors/discover/__init__.py

Discover statement processor support.
"""

from __future__ import annotations

from .checking import DiscoverCheckingProcessor
from .signatures import DISCOVER_CHECKING_SIGNATURES, DISCOVER_SIGNATURES

__all__ = [
    "DISCOVER_CHECKING_SIGNATURES",
    "DISCOVER_SIGNATURES",
    "DiscoverCheckingProcessor",
]
