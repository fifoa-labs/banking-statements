"""
tests/processors/penfed/heloc/test_summary.py

Tests for PenFed HELOC account-summary parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.processors.penfed.heloc.summary import (
    parse_balance_summary,
    parse_summary,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def summary_text(  # noqa: PLR0913
    *,
    opening: str = "$1,000.00",
    advances: str = "$25.00",
    interest: str = "$10.00",
    payments: str = "-$100.00",
    adjustment: str = "$0.00",
    closing: str = "$935.00",
) -> str:
    """Build a synthetic PenFed HELOC account summary."""
    return (
        f"Previous Balance {opening}\n"
        f"Advances and Fees {advances}\n"
        f"Interest Charges {interest}\n"
        f"Payment and Other Credits {payments}\n"
        f"Debit/Credit Adjustment {adjustment}\n"
        f"New Balance as of 03/19/26 {closing}\n"
    )


def test_parse_summary_and_balance_summary() -> None:
    summary = parse_summary(make_text(summary_text()))

    assert summary.balances.opening_balance == Decimal("1000.00")
    assert summary.balances.closing_balance == Decimal("935.00")
    assert summary.advances_and_fees == Decimal("25.00")
    assert summary.interest_charges == Decimal("10.00")
    assert summary.payment_and_other_credits == Decimal("-100.00")
    assert summary.debit_credit_adjustment == Decimal("0.00")
    assert parse_balance_summary(make_text(summary_text())) == summary.balances


def test_parse_summary_accepts_parenthesized_credit_values() -> None:
    summary = parse_summary(
        make_text(
            summary_text(
                opening="($25.00)",
                advances="$0.00",
                interest="$0.00",
                payments="$0.00",
                closing="($25.00)",
            )
        )
    )

    assert summary.balances.opening_balance == Decimal("-25.00")
    assert summary.balances.closing_balance == Decimal("-25.00")


@pytest.mark.parametrize(
    "missing_field",
    [
        "opening_balance",
        "advances_and_fees",
        "interest_charges",
        "payment_and_other_credits",
        "debit_credit_adjustment",
        "closing_balance",
    ],
)
def test_parse_summary_requires_all_fields(missing_field: str) -> None:
    lines = {
        "opening_balance": "Previous Balance $1,000.00",
        "advances_and_fees": "Advances and Fees $0.00",
        "interest_charges": "Interest Charges $10.00",
        "payment_and_other_credits": "Payment and Other Credits -$100.00",
        "debit_credit_adjustment": "Debit/Credit Adjustment $0.00",
        "closing_balance": "New Balance as of 03/19/26 $910.00",
    }
    value = "\n".join(
        line for field, line in lines.items() if field != missing_field
    )

    with pytest.raises(ValueError, match=missing_field):
        parse_summary(make_text(value))


def test_parse_summary_requires_unique_field_value() -> None:
    with pytest.raises(ValueError, match="interest_charges.*uniquely"):  # noqa: RUF043
        parse_summary(make_text(summary_text() + "Interest Charges $11.00\n"))


def test_parse_summary_must_reconcile() -> None:
    with pytest.raises(ValueError, match="summary does not reconcile"):
        parse_summary(make_text(summary_text(closing="$936.00")))
