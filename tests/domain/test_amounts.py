"""
tests/domain/test_amounts.py

Tests for financial amount normalization.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from banking_statements.domain import to_decimal


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("12.34"), Decimal("12.34")),
        (12, Decimal("12")),
        ("12.34", Decimal("12.34")),
        ("$12.34", Decimal("12.34")),
        ("-$12.34", Decimal("-12.34")),
        ("1,234.56", Decimal("1234.56")),
        ("(12.34)", Decimal("-12.34")),
        ("($12.34)", Decimal("-12.34")),
    ],
)
def test_to_decimal(
    value: Decimal | int | str,
    expected: Decimal,
) -> None:
    assert to_decimal(value) == expected


@pytest.mark.parametrize("value", ["", "   ", "not-money"])
def test_to_decimal_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        to_decimal(value)
