"""
src/banking_statements/processors/wellsfargo/checking/__init__.py

Wells Fargo checking statement processor support.
"""

from __future__ import annotations

from .identity import WellsFargoCheckingIdentity, parse_identity
from .processor import WellsFargoCheckingProcessor
from .sections import extract_checking_section
from .summary import parse_balance_summary

__all__ = [
    "WellsFargoCheckingIdentity",
    "WellsFargoCheckingProcessor",
    "extract_checking_section",
    "parse_balance_summary",
    "parse_identity",
]
