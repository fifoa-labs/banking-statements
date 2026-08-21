"""
tests/processors/penfed/heloc/activity/test_transactions.py

Tests for PenFed HELOC transaction normalization.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from banking_statements.domain import (
    StatementPeriod,
    StatementSource,
    TransactionDirection,
)
from banking_statements.processors.penfed.heloc.activity import (
    PenFedHelocActivityKind,
    PenFedHelocActivityRow,
    parse_activity_transactions,
)


def make_period() -> StatementPeriod:
    """Build a synthetic PenFed HELOC statement period."""
    return StatementPeriod(
        start=date(2026, 2, 19),
        end=date(2026, 3, 19),
    )


def make_source() -> StatementSource:
    """Build a synthetic statement source."""
    return StatementSource(
        path=Path("sample-penfed-heloc.pdf"),
        sha256="a" * 64,
    )


def make_row(
    *,
    process_date: str = "03/10/26",
    effective_date: str | None = None,
    amount: Decimal | None = Decimal("100.00"),
    direction: TransactionDirection | None = TransactionDirection.CREDIT,
    description: str = "PRINCIPAL CURTAILMENT PAYMENT",
) -> PenFedHelocActivityRow:
    """Build one synthetic PenFed activity row."""
    return PenFedHelocActivityRow(
        process_date=process_date,
        effective_date=effective_date,
        kind=PenFedHelocActivityKind.PRINCIPAL_CURTAILMENT,
        description=description,
        total_amount=Decimal("100.00"),
        principal_applied=Decimal("100.00"),
        interest=Decimal("0.00"),
        escrow=Decimal("0.00"),
        fees=Decimal("0.00"),
        other=Decimal("0.00"),
        amount=amount,
        direction=direction,
        raw_text="synthetic row",
    )


def test_parse_activity_transactions_prefers_effective_date_and_evidence() -> (
    None
):
    transaction = parse_activity_transactions(
        (
            make_row(
                process_date="03/10/26",
                effective_date="03/11/26",
            ),
        ),
        period=make_period(),
        source=make_source(),
        finance_charges=Decimal("0.00"),
        finance_raw_text="Total Finance Charge $0.00",
    )[0]

    assert transaction.date == date(2026, 3, 11)
    assert transaction.amount == Decimal("100.00")
    assert transaction.direction is TransactionDirection.CREDIT
    assert transaction.description == "PRINCIPAL CURTAILMENT PAYMENT"
    assert transaction.evidence is not None
    assert transaction.evidence.source == make_source()
    assert transaction.evidence.section == "Transaction Activity"
    assert transaction.evidence.raw_text == "synthetic row"
    assert transaction.evidence.processor == "penfed.heloc.v1"
    assert transaction.evidence.sequence == 1


def test_parse_activity_transactions_uses_process_date_and_adds_finance() -> (
    None
):
    transactions = parse_activity_transactions(
        (
            make_row(),
            make_row(
                amount=None,
                direction=None,
                description="PAYMENT RECEIVED",
            ),
        ),
        period=make_period(),
        source=make_source(),
        finance_charges=Decimal("12.50"),
        finance_raw_text="Total Finance Charge $12.50",
    )

    assert len(transactions) == 2
    assert transactions[0].date == date(2026, 3, 10)

    finance = transactions[1]
    assert finance.date == make_period().end
    assert finance.amount == Decimal("12.50")
    assert finance.direction is TransactionDirection.DEBIT
    assert finance.description == "FINANCE CHARGES"
    assert finance.evidence is not None
    assert finance.evidence.section == "FINANCE CHARGES"
    assert finance.evidence.raw_text == "Total Finance Charge $12.50"
    assert finance.evidence.sequence == 2


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (
            make_row(amount=None, direction=TransactionDirection.CREDIT),
            "incomplete transaction semantics",
        ),
        (
            make_row(amount=Decimal("0.00")),
            "amount must be positive",
        ),
        (
            make_row(process_date="02/30/26"),
            "calendar date",
        ),
        (
            make_row(process_date="04/01/26"),
            "outside statement period",
        ),
    ],
)
def test_parse_activity_transactions_rejects_invalid_rows(
    row: PenFedHelocActivityRow,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_activity_transactions(
            (row,),
            period=make_period(),
            source=make_source(),
            finance_charges=Decimal("0.00"),
            finance_raw_text="Total Finance Charge $0.00",
        )


def test_parse_activity_transactions_rejects_negative_finance_charge() -> None:
    with pytest.raises(ValueError, match="finance charges"):
        parse_activity_transactions(
            (),
            period=make_period(),
            source=make_source(),
            finance_charges=Decimal("-1.00"),
            finance_raw_text="Total Finance Charge -$1.00",
        )


def test_parse_activity_transactions_returns_empty() -> None:
    assert (
        parse_activity_transactions(
            (),
            period=make_period(),
            source=make_source(),
            finance_charges=Decimal("0.00"),
            finance_raw_text="Total Finance Charge $0.00",
        )
        == ()
    )
