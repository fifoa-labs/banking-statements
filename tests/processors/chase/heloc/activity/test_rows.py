"""
tests/processors/chase/heloc/activity/test_rows.py

Tests for Chase HELOC transaction-activity row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.domain import TransactionDirection
from banking_statements.processors.chase.heloc.activity import (
    ChaseHelocActivityKind,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def activity(*rows: str) -> StatementText:
    """Build synthetic Chase HELOC transaction activity."""
    return make_text(
        "\n".join(
            (
                "Transaction activity",
                "Transaction Description Total received Principal Interest",
                *rows,
                "Additional information",
            )
        )
    )


def test_parse_economic_activity_rows() -> None:
    rows = parse_activity_rows(
        activity(
            "01/22/2026 INITIAL FUNDING Revolving $0.00 ($8,000.00)",
            "01/23/2026 FIN CHARGE-ORIG FEE ASSES $0.00 $25.00",
            "01/25/2026 ADDITIONAL PRINCIPAL PYMT $500.00 $500.00",
            "01/26/2026 FIN CHARGE-ORIG FEE PAID $25.00 $25.00",
            "02/01/2026 BALANCE ADVANCE Revolving $0.00 ($1,500.00)",
        )
    )

    assert [row.kind for row in rows] == [
        ChaseHelocActivityKind.INITIAL_FUNDING,
        ChaseHelocActivityKind.FEE_ASSESSED,
        ChaseHelocActivityKind.ADDITIONAL_PRINCIPAL_PAYMENT,
        ChaseHelocActivityKind.FEE_PAID,
        ChaseHelocActivityKind.BALANCE_ADVANCE,
    ]
    assert [row.amount for row in rows] == [
        Decimal("8000.00"),
        Decimal("25.00"),
        Decimal("500.00"),
        Decimal("25.00"),
        Decimal("1500.00"),
    ]
    assert [row.direction for row in rows] == [
        TransactionDirection.DEBIT,
        TransactionDirection.DEBIT,
        TransactionDirection.CREDIT,
        TransactionDirection.CREDIT,
        TransactionDirection.DEBIT,
    ]


def test_payment_allocation_is_informational() -> None:
    rows = parse_activity_rows(
        activity(
            "02/10/2026 PAYMENT Revolving $0.00 $40.00 $60.00",
            "02/10/2026 FUNDS APPLIED Revolving $100.00",
        )
    )

    assert rows[0].kind is ChaseHelocActivityKind.PAYMENT_ALLOCATION
    assert rows[0].amount is None
    assert rows[0].direction is None

    assert rows[1].kind is ChaseHelocActivityKind.FUNDS_APPLIED
    assert rows[1].amount == Decimal("100.00")
    assert rows[1].direction is TransactionDirection.CREDIT


def test_zero_received_funds_applied_is_internal_reallocation() -> None:
    rows = parse_activity_rows(
        activity(
            "02/10/2026 FUNDS APPLIED Revolving $0.00 ($75.00)",
        )
    )

    assert rows[0].amount is None
    assert rows[0].direction is None


def test_parse_activity_rows_returns_empty_for_no_activity() -> None:
    assert (
        parse_activity_rows(
            make_text(
                "Transaction activity\n"
                "Transaction Description Total received Principal Interest\n"
                "Additional information\n"
            )
        )
        == ()
    )


def test_parse_activity_rows_returns_empty_without_section() -> None:
    assert parse_activity_rows(make_text("Account summary")) == ()


def test_parse_activity_rows_rejects_unknown_dated_row() -> None:
    with pytest.raises(
        ValueError,
        match="Unrecognized Chase HELOC transaction row",
    ):
        parse_activity_rows(activity("02/10/2026 UNKNOWN ACTIVITY $25.00"))


def test_fee_assessment_requires_nonzero_amount() -> None:
    with pytest.raises(ValueError, match="no non-zero amount"):
        parse_activity_rows(
            activity("02/10/2026 FIN CHARGE-ORIG FEE ASSES $0.00")
        )


def test_principal_payment_requires_positive_received_amount() -> None:
    with pytest.raises(ValueError, match="invalid received amount"):
        parse_activity_rows(
            activity("02/10/2026 ADDITIONAL PRINCIPAL PYMT $0.00 $0.00")
        )


def test_funds_applied_requires_amount() -> None:
    with pytest.raises(ValueError, match="funds-applied row has no amount"):
        parse_activity_rows(activity("02/10/2026 FUNDS APPLIED Revolving"))


def test_funds_applied_rejects_negative_received_amount() -> None:
    with pytest.raises(ValueError, match="must not be negative"):
        parse_activity_rows(
            activity("02/10/2026 FUNDS APPLIED Revolving ($10.00)")
        )


def test_undated_fee_assessment_uses_preceding_transaction_date() -> None:
    rows = parse_activity_rows(
        activity(
            "01/22/2026 INITIAL FUNDING Revolving $0.00 ($8,000.00)",
            "FIN CHARGE-ORIG FEE ASSES $0.00 $25.00",
        )
    )

    assert len(rows) == 2
    assert rows[1].transaction_date == "01/22/2026"
    assert rows[1].kind is ChaseHelocActivityKind.FEE_ASSESSED
    assert rows[1].amount == Decimal("25.00")
    assert rows[1].direction is TransactionDirection.DEBIT


def test_undated_activity_without_preceding_date_is_rejected() -> None:
    with pytest.raises(ValueError, match="no preceding transaction date"):
        parse_activity_rows(activity("FIN CHARGE-ORIG FEE ASSES $0.00 $25.00"))


def test_activity_section_can_run_to_end_of_statement() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transaction activity\n"
            "Transaction Description Total received Principal Interest\n"
            "02/10/2026 BALANCE ADVANCE Revolving $0.00 ($500.00)"
        )
    )

    assert len(rows) == 1
    assert rows[0].kind is ChaseHelocActivityKind.BALANCE_ADVANCE
    assert rows[0].amount == Decimal("500.00")


def test_principal_payment_requires_amount() -> None:
    with pytest.raises(ValueError, match="activity row has no amount"):
        parse_activity_rows(activity("02/10/2026 ADDITIONAL PRINCIPAL PYMT"))


def test_funds_reversed_is_informational() -> None:
    rows = parse_activity_rows(
        activity("08/22/2026 FUNDS REVERSED Revolving $0.00 $52.93")
    )

    assert len(rows) == 1
    assert rows[0].kind is ChaseHelocActivityKind.FUNDS_REVERSED
    assert rows[0].amount is None
    assert rows[0].direction is None
