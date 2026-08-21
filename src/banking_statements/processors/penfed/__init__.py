"""
src/banking_statements/processors/penfed/__init__.py

PenFed statement processor support.
"""

from __future__ import annotations

from .heloc import PenFedHelocProcessor
from .signatures import PENFED_HELOC_SIGNATURES, PENFED_SIGNATURES

__all__ = [
    "PENFED_HELOC_SIGNATURES",
    "PENFED_SIGNATURES",
    "PenFedHelocProcessor",
]
