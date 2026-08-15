"""
src/banking_statements/text/__init__.py

Public text extraction contracts and models.
"""

from __future__ import annotations

from .models import StatementPage, StatementText
from .pdf import PdfStatementTextReader
from .readers import StatementTextReader

__all__ = [
    "PdfStatementTextReader",
    "StatementPage",
    "StatementText",
    "StatementTextReader",
]
