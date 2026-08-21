"""
tests/processors/penfed/heloc/activity/test_rows.py

Tests for PenFed HELOC logical transaction-activity row parsing.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.domain import TransactionDirection
from banking_statements.processors.penfed.heloc.activity import (
    PenFedHelocActivityKind,
    parse_activity_rows,
)
from banking_statements.text import StatementPage, StatementText


def make_text(value: str) -> StatementText:
    """Build one-page synthetic statement text."""
    return StatementText(pages=(StatementPage(number=1, text=value),))


def activity(*rows: str) -> StatementText:
    """Build synthetic PenFed HELOC transaction activity."""
    return make_text(
        "\n".join(
            (
                "Transaction Activity (02/19/26 through 03/19/26)",
                "Total Principal Charges/ Unapplied/",
                "Date Description Amount Applied Interest Escrow Fees Other",
                *rows,
                "FINANCE CHARGES",
            )
        )
    )


def test_parse_legacy_payment_and_principal_rows() -> None:
    rows = parse_activity_rows(
        activity(
            "03/13/26 PRINCIPAL CURTAILMENT PAYMENT "
            "$100.00 $100.00 $0.00 $0.00 $0.00 $0.00",
            "03/13/26 PAYMENT RECEIVED (NON-LOCKBOX) "
            "$0.00 $0.00 $1,250.00 $0.00 $0.00 $0.00",
            "03/13/26 PAYMENT RECEIVED (NON-LOCKBOX) "
            "$1,250.00 $0.00 $0.00 $0.00 $0.00 $0.00",
        )
    )

    assert len(rows) == 3

    principal, allocation, payment = rows

    assert principal.kind is PenFedHelocActivityKind.PRINCIPAL_CURTAILMENT
    assert principal.amount == Decimal("100.00")
    assert principal.direction is TransactionDirection.CREDIT
    assert principal.effective_date is None

    assert allocation.kind is PenFedHelocActivityKind.PAYMENT_RECEIVED
    assert allocation.amount is None
    assert allocation.direction is None
    assert allocation.interest == Decimal("1250.00")

    assert payment.amount == Decimal("1250.00")
    assert payment.direction is TransactionDirection.CREDIT


def test_parse_current_process_and_effective_date_rows() -> None:
    rows = parse_activity_rows(
        activity(
            "03/13/26 03/14/26 PAYMENT RECEIVED "
            "$500.00 $0.00 $0.00 $0.00 $0.00 $0.00",
        )
    )

    assert len(rows) == 1
    assert rows[0].process_date == "03/13/26"
    assert rows[0].effective_date == "03/14/26"
    assert rows[0].description == "PAYMENT RECEIVED"
    assert rows[0].amount == Decimal("500.00")


def test_parse_returned_check_fee_and_reversal_rows() -> None:
    rows = parse_activity_rows(
        activity(
            "03/10/26 RETURNED CHECK FEE $0.00 $0.00 $0.00 $0.00 $30.00 $0.00",
            "03/11/26 RETURNED CHECK FEE "
            "$0.00 $0.00 $0.00 $0.00 ($30.00) $0.00",
            "03/11/26 NSF/RETURNED CHECK REVERSAL "
            "$0.00 ($100.00) ($500.00) $0.00 $0.00 $0.00",
        )
    )

    fee, fee_reversal, payment_reversal = rows

    assert fee.kind is PenFedHelocActivityKind.RETURNED_CHECK_FEE
    assert fee.amount == Decimal("30.00")
    assert fee.direction is TransactionDirection.DEBIT

    assert fee_reversal.amount == Decimal("30.00")
    assert fee_reversal.direction is TransactionDirection.CREDIT

    assert (
        payment_reversal.kind
        is PenFedHelocActivityKind.NSF_RETURNED_CHECK_REVERSAL
    )
    assert payment_reversal.amount == Decimal("600.00")
    assert payment_reversal.direction is TransactionDirection.DEBIT


def test_parse_activity_rows_across_repeated_blocks() -> None:
    rows = parse_activity_rows(
        make_text(
            "Transaction Activity (02/19/26 through 03/19/26)\n"
            "03/10/26 PRINCIPAL CURTAILMENT PAYMENT "
            "$100.00 $100.00 $0.00 $0.00 $0.00 $0.00\n"
            "Informational autopay content\n"
            "Transaction Activity (02/19/26 through 03/19/26)\n"
            "03/11/26 PAYMENT RECEIVED "
            "$500.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
            "FINANCE CHARGES\n"
            "03/12/26 PAYMENT RECEIVED "
            "$25.00 $0.00 $0.00 $0.00 $0.00 $0.00\n"
        )
    )

    assert len(rows) == 2
    assert rows[0].description == "PRINCIPAL CURTAILMENT PAYMENT"
    assert rows[1].description == "PAYMENT RECEIVED"


def test_parse_activity_rows_returns_empty_without_activity() -> None:
    assert parse_activity_rows(make_text("FINANCE CHARGES")) == ()


def test_parse_activity_rows_rejects_malformed_dated_row() -> None:
    with pytest.raises(ValueError, match="Unrecognized PenFed HELOC"):
        parse_activity_rows(activity("03/10/26 MALFORMED ACTIVITY"))


def test_parse_activity_rows_rejects_unknown_description() -> None:
    with pytest.raises(ValueError, match="Unsupported PenFed HELOC"):
        parse_activity_rows(
            activity(
                "03/10/26 UNKNOWN ACTIVITY "
                "$10.00 $0.00 $0.00 $0.00 $0.00 $0.00"
            )
        )


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (
            (
                "03/10/26 PRINCIPAL CURTAILMENT PAYMENT "
                "$0.00 $0.00 $0.00 $0.00 $0.00 $0.00"
            ),
            "principal curtailment",
        ),
        (
            (
                "03/10/26 PRINCIPAL CURTAILMENT PAYMENT "
                "$100.00 $90.00 $0.00 $0.00 $0.00 $0.00"
            ),
            "principal curtailment",
        ),
        (
            (
                "03/10/26 PRINCIPAL CURTAILMENT PAYMENT "
                "$100.00 $100.00 $1.00 $0.00 $0.00 $0.00"
            ),
            "principal curtailment",
        ),
        (
            "03/10/26 PAYMENT RECEIVED $100.00 $1.00 $0.00 $0.00 $0.00 $0.00",
            "payment received",
        ),
        (
            "03/10/26 PAYMENT RECEIVED -$100.00 $0.00 $0.00 $0.00 $0.00 $0.00",
            "payment received",
        ),
        (
            "03/10/26 PAYMENT RECEIVED $0.00 $0.00 $0.00 $0.00 $0.00 $0.00",
            "payment allocation",
        ),
        (
            "03/10/26 PAYMENT RECEIVED $0.00 $0.00 ($1.00) $0.00 $0.00 $0.00",
            "payment allocation",
        ),
        (
            "03/10/26 RETURNED CHECK FEE $1.00 $0.00 $0.00 $0.00 $30.00 $0.00",
            "returned-check fee",
        ),
        (
            "03/10/26 RETURNED CHECK FEE $0.00 $0.00 $0.00 $0.00 $0.00 $0.00",
            "returned-check fee",
        ),
        (
            (
                "03/10/26 NSF/RETURNED CHECK REVERSAL "
                "$0.00 $0.00 $0.00 $0.00 $0.00 $0.00"
            ),
            "NSF reversal",
        ),
        (
            (
                "03/10/26 NSF/RETURNED CHECK REVERSAL "
                "$0.00 $1.00 $0.00 $0.00 $0.00 $0.00"
            ),
            "NSF reversal",
        ),
    ],
)
def test_parse_activity_rows_rejects_invalid_economic_shapes(
    line: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_activity_rows(activity(line))
