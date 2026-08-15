"""
tests/processors/wellsfargo/checking/test_summary.py

Tests for Wells Fargo checking balance summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.wellsfargo.checking.summary import (
    parse_balance_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for balance summary tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_parse_balance_summary() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Wells Fargo College Checking®",
                    "Beginning balance on 12/14 $1,234.56",
                    "Ending balance on 1/14 $987.65",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("1234.56")
    assert summary.closing_balance == Decimal("987.65")


def test_parse_balance_summary_handles_extraction_spacing() -> None:
    summary = parse_balance_summary(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Wells Far go College Checking®",
                    "Beginning b alance on 12/14 $3,736.09",
                    "Ending bal ance on 1/14 2,207.85",
                )
            )
        )
    )

    assert summary.opening_balance == Decimal("3736.09")
    assert summary.closing_balance == Decimal("2207.85")


def test_parse_balance_summary_rejects_missing_beginning_balance() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo checking beginning balance was not found",
    ):
        parse_balance_summary(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Wells Fargo College Checking®",
                        "Ending balance on 1/14 $987.65",
                    )
                )
            )
        )


def test_parse_balance_summary_rejects_missing_ending_balance() -> None:
    with pytest.raises(
        ValueError,
        match="Wells Fargo checking ending balance was not found",
    ):
        parse_balance_summary(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Wells Fargo College Checking®",
                        "Beginning balance on 12/14 $1,234.56",
                    )
                )
            )
        )
