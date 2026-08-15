"""
src/banking_statements/processors/wellsfargo/credit_card/activity/rows.py

Layout-aware activity-row parsing for Wells Fargo credit-card statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.text import (
        StatementPage,
        StatementText,
        StatementWord,
    )


@dataclass(frozen=True, slots=True)
class WellsFargoCreditCardActivityRow:
    """One normalized Wells Fargo credit-card activity row."""

    card_last4: str
    transaction_date: str
    post_date: str
    reference_number: str
    description: str
    credit: Decimal | None
    charge: Decimal | None


@dataclass(frozen=True, slots=True)
class _ActivityColumns:
    """Horizontal anchors for Wells Fargo card monetary columns."""

    credit_x: float
    charge_x: float


_DATE_PATTERN = re.compile(r"^\d{2}/\d{2}$")
_CARD_PATTERN = re.compile(r"^\d{4}$")
_AMOUNT_PATTERN = re.compile(r"^-?[\d,]+\.\d{2}$")

_TRANSACTION_HEADING_PATTERN = re.compile(
    r"Transactions?(?:\s|\(|$)",
    re.IGNORECASE,
)

_IGNORED_PREFIXES = (
    "Card Trans Post Reference",
    "Ending Date Date",
    "Purchases, Balance Transfers",
    "Payments",
    "Other Credits",
    "Cash Advances",
    "Fees Charged",
    "Interest Charged",
    "TOTAL ",
    "INTEREST CHARGE ",
    "Interest Charge Calculation",
    "Annual Days in",
    "Type of Balance",
    "2024 Totals Year-to-Date",
    "2025 Totals Year-to-Date",
    "2026 Totals Year-to-Date",
)

_LINE_TOLERANCE = 3.0


def _parse_amount(value: str) -> Decimal:
    """Parse a Wells Fargo credit-card monetary amount."""
    return Decimal(value.replace(",", ""))


def _group_words_by_line(
    words: Sequence[StatementWord],
) -> tuple[tuple[StatementWord, ...], ...]:
    """Group positioned PDF words into visual lines."""
    lines: list[list[StatementWord]] = []

    for word in sorted(words, key=lambda item: (item.top, item.x0)):
        if not lines:
            lines.append([word])
            continue

        previous_line = lines[-1]
        line_top = min(item.top for item in previous_line)

        if abs(word.top - line_top) <= _LINE_TOLERANCE:
            previous_line.append(word)
        else:
            lines.append([word])

    return tuple(
        tuple(sorted(line, key=lambda item: item.x0)) for line in lines
    )


def _line_text(words: Sequence[StatementWord]) -> str:
    """Return text reconstructed from one visual line."""
    return " ".join(word.text for word in words)


def _find_columns(
    line: Sequence[StatementWord],
) -> _ActivityColumns | None:
    """Locate Credits and Charges anchors in a table header."""
    credit = next(
        (word for word in line if word.text.casefold() == "credits"),
        None,
    )
    charge = next(
        (word for word in line if word.text.casefold() == "charges"),
        None,
    )

    if credit is None or charge is None:
        return None

    return _ActivityColumns(
        credit_x=credit.x0,
        charge_x=charge.x0,
    )


def _amount_column(
    word: StatementWord,
    *,
    columns: _ActivityColumns,
) -> str:
    """Return the nearest Wells Fargo monetary column."""
    center = (word.x0 + word.x1) / 2

    credit_distance = abs(center - columns.credit_x)
    charge_distance = abs(center - columns.charge_x)

    return "credit" if credit_distance < charge_distance else "charge"


def _parse_transaction_line(
    words: Sequence[StatementWord],
    *,
    columns: _ActivityColumns,
) -> WellsFargoCreditCardActivityRow | None:
    """Parse one Wells Fargo credit-card transaction line."""
    if len(words) < 4:  # noqa: PLR2004
        return None

    if _CARD_PATTERN.fullmatch(words[0].text) is not None:
        if len(words) < 5:  # noqa: PLR2004
            return None

        card_last4 = words[0].text
        transaction_index = 1
        post_index = 2
        reference_index = 3
        description_index = 4
    else:
        card_last4 = ""
        transaction_index = 0
        post_index = 1
        reference_index = 2
        description_index = 3

    if _DATE_PATTERN.fullmatch(words[transaction_index].text) is None:
        return None

    if _DATE_PATTERN.fullmatch(words[post_index].text) is None:
        return None

    amount_words = tuple(
        word
        for word in words[description_index:]
        if _AMOUNT_PATTERN.fullmatch(word.text)
        and word.x0 >= columns.credit_x - 20
    )

    if len(amount_words) != 1:
        msg = (
            "Wells Fargo credit-card transaction row must contain exactly "
            f"one credit or charge amount: {_line_text(words)}"
        )
        raise ValueError(msg)

    amount_word = amount_words[0]
    column = _amount_column(
        amount_word,
        columns=columns,
    )
    amount = _parse_amount(amount_word.text)

    description_words = tuple(
        word.text
        for word in words[description_index:]
        if word is not amount_word
    )

    return WellsFargoCreditCardActivityRow(
        card_last4=card_last4,
        transaction_date=words[transaction_index].text,
        post_date=words[post_index].text,
        reference_number=words[reference_index].text,
        description=" ".join(description_words),
        credit=amount if column == "credit" else None,
        charge=amount if column == "charge" else None,
    )


def _parse_page_rows(
    page: StatementPage,
) -> tuple[WellsFargoCreditCardActivityRow, ...]:
    """Parse activity rows from one Wells Fargo credit-card page."""
    lines = _group_words_by_line(page.words)

    rows: list[WellsFargoCreditCardActivityRow] = []
    in_transactions = False
    columns: _ActivityColumns | None = None

    for line in lines:
        line_text = _line_text(line)

        if _TRANSACTION_HEADING_PATTERN.match(line_text):
            in_transactions = True
            columns = None
            continue

        if not in_transactions:
            continue

        discovered_columns = _find_columns(line)
        if discovered_columns is not None:
            columns = discovered_columns
            continue

        if columns is None:
            continue

        if line_text.startswith(_IGNORED_PREFIXES):
            continue

        row = _parse_transaction_line(
            line,
            columns=columns,
        )

        if row is not None:
            rows.append(row)
            continue

        if rows:
            previous = rows[-1]

            rows[-1] = replace(
                previous,
                description=(f"{previous.description} {line_text}".strip()),
            )

    return tuple(rows)


def parse_activity_rows(
    text: StatementText,
) -> tuple[WellsFargoCreditCardActivityRow, ...]:
    """Parse layout-aware Wells Fargo credit-card activity rows."""
    rows: list[WellsFargoCreditCardActivityRow] = []

    for page in text.pages:
        rows.extend(_parse_page_rows(page))

    return tuple(rows)
