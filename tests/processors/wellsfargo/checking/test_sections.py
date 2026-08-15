"""
tests/processors/wellsfargo/checking/test_sections.py

Tests for Wells Fargo checking section extraction.
"""

from __future__ import annotations

import pytest

from banking_statements.processors.wellsfargo.checking.sections import (
    extract_checking_section,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for section tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_extract_checking_section_from_combined_statement() -> None:
    section = extract_checking_section(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Summary of accounts",
                    "Wells Far go College Checking®",
                    "Activity summary Account number: 1234567890",
                    "Transaction history",
                    "12/20 Transfer From Sample Payroll 200.00 1,200.00",
                    "Monthly service fee summary",
                    "Fee period 12/14/2018 - 01/14/2019",
                    "Wells Fargo Way2Save® Savings",
                    "Activity summary Account number: 0987654321",
                    "Transaction history",
                    "12/21 Recurring Transfer From Sample Checking 25.00 125.00",  # noqa: E501
                )
            )
        )
    )

    assert "Wells Far go College Checking®" in section
    assert "Activity summary Account number: 1234567890" in section
    assert "Transfer From Sample Payroll" in section
    assert "Fee period 12/14/2018 - 01/14/2019" in section

    assert "Wells Fargo Way2Save® Savings" not in section
    assert "0987654321" not in section
    assert "Recurring Transfer From Sample Checking" not in section


def test_extract_checking_section_without_following_savings_section() -> None:
    section = extract_checking_section(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Statement header",
                    "Wells Fargo College Checking®",
                    "Activity summary Account number: 1234567890",
                    "Transaction history",
                    "12/20 Transfer From Sample Payroll 200.00 1,200.00",
                    "Monthly service fee summary",
                    "Fee period 12/14/2018 - 01/14/2019",
                )
            )
        )
    )

    assert section.startswith("Wells Fargo College Checking®")
    assert "Transfer From Sample Payroll" in section
    assert "Fee period 12/14/2018 - 01/14/2019" in section


def test_extract_checking_section_rejects_missing_checking_section() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo checking section was not found",
    ):
        extract_checking_section(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Wells Fargo Way2Save® Savings",
                        "Activity summary Account number: 0987654321",
                    )
                )
            )
        )
