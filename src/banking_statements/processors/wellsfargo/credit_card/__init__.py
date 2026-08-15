"""
src/banking_statements/processors/wellsfargo/credit_card/__init__.py

Wells Fargo credit-card statement processor support.
"""

from __future__ import annotations

from .identity import WellsFargoCreditCardIdentity, parse_identity
from .processor import WellsFargoCreditCardProcessor
from .summary import parse_balance_summary

__all__ = [
    "WellsFargoCreditCardIdentity",
    "WellsFargoCreditCardProcessor",
    "parse_balance_summary",
    "parse_identity",
]
