"""
src/banking_statements/domain/amounts.py

Decimal normalization helpers for financial values.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def to_decimal(value: Decimal | int | str) -> Decimal:
    """Convert a supported financial value to Decimal."""
    if isinstance(value, Decimal):
        return value

    if isinstance(value, int):
        return Decimal(value)

    text = value.strip().replace(",", "")

    if not text:
        message = "Financial value cannot be empty."
        raise ValueError(message)

    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()

    if text.startswith("$"):
        text = text[1:].strip()

    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        message = f"Invalid financial value: {value!r}."
        raise ValueError(message) from exc

    if negative:
        return -amount

    return amount
