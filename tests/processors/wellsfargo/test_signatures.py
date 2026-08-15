"""
tests/processors/wellsfargo/test_signatures.py

Tests for Wells Fargo institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.detection import InstitutionDetector
from banking_statements.processors.wellsfargo import WELLS_FARGO_SIGNATURES
from banking_statements.text import StatementPage, StatementText


def test_wells_fargo_signature_detects_statement() -> None:
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text=(
                    "Wells Fargo Bank, N.A.\n"
                    "Online banking available at wellsfargo.com\n"
                ),
            ),
        )
    )

    detector = InstitutionDetector(WELLS_FARGO_SIGNATURES)

    assert detector.detect(text) == "wellsfargo"
