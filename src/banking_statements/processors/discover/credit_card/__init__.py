"""
src/banking_statements/processors/discover/credit_card/__init__.py

Discover credit-card statement processor support.
"""

from __future__ import annotations

from .identity import DiscoverCreditCardIdentity, parse_identity
from .processor import DiscoverCreditCardProcessor
from .summary import parse_balance_summary

__all__ = [
    "DiscoverCreditCardIdentity",
    "DiscoverCreditCardProcessor",
    "parse_balance_summary",
    "parse_identity",
]
