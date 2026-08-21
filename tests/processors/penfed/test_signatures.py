"""
tests/processors/penfed/test_signatures.py

Tests for PenFed institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.penfed import (
    PENFED_HELOC_SIGNATURES,
    PENFED_SIGNATURES,
)


def test_penfed_heloc_signature_is_stable() -> None:
    assert len(PENFED_HELOC_SIGNATURES) == 1

    signature = PENFED_HELOC_SIGNATURES[0]

    assert signature.institution == "penfed"
    assert signature.required_markers == (
        "Home Equity Line of Credit Statement",
        "Statement Closing Date:",
        "Loan Number ",
        "CURRENT ACCOUNT INFORMATION",
        "HELOC ACTIVITY AND FINANCE CHARGES",
        "Transaction Activity (",
        "FINANCE CHARGES",
        "www.PenFed.org",
    )


def test_penfed_signatures_include_all_account_families() -> None:
    assert (*PENFED_HELOC_SIGNATURES,) == PENFED_SIGNATURES
