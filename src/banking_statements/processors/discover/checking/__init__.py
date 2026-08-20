"""
src/banking_statements/processors/discover/checking/__init__.py

Discover checking statement processor support.
"""

from __future__ import annotations

from .identity import DiscoverCheckingIdentity, parse_identity
from .processor import DiscoverCheckingProcessor
from .summary import parse_balance_summary

__all__ = [
    "DiscoverCheckingIdentity",
    "DiscoverCheckingProcessor",
    "parse_balance_summary",
    "parse_identity",
]
