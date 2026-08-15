"""
src/banking_statements/processors/wellsfargo/business_checking/activity/rows.py

Layout-aware activity parsing for Wells Fargo business checking statements.
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
class WellsFargoBusinessCheckingActivityRow:
    """Normalized Wells Fargo business checking activity row."""

    transaction_date: str
    description: str
    credit: Decimal | None
    debit: Decimal | None
    balance: Decimal | None


@dataclass(frozen=True, slots=True)
class _ActivityColumns:
    """Horizontal anchors for business checking monetary columns."""

    credit_x: float
    debit_x: float
    balance_x: float


_DATE_PATTERN = re.compile(
    r"^\d{1,2}/\d{1,2}$",
)

_AMOUNT_PATTERN = re.compile(
    r"^-?[\d,]+\.\d{2}$",
)

_TRANSACTION_HISTORY_PATTERN = re.compile(
    r"Transaction\s+history",
    re.IGNORECASE,
)

_SECTION_END_PREFIXES = (
    "Ending balance on ",
    "Totals ",
    "Monthly service fee summary",
)

_LINE_TOLERANCE = 3.0


def _parse_amount(value: str) -> Decimal:
    """Parse a Wells Fargo business checking monetary amount."""
    return Decimal(value.replace(",", ""))


def _group_words_by_line(
    words: Sequence[StatementWord],
) -> tuple[tuple[StatementWord, ...], ...]:
    """Group positioned words into visual PDF lines."""
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


def _line_text(
    words: Sequence[StatementWord],
) -> str:
    """Return reconstructed visual-line text."""
    return " ".join(word.text for word in words)


def _find_columns(
    line: Sequence[StatementWord],
) -> _ActivityColumns | None:
    """Find Credits, Debits, and balance column anchors."""
    credit = next(
        (word for word in line if word.text.casefold() == "credits"),
        None,
    )
    debit = next(
        (word for word in line if word.text.casefold() == "debits"),
        None,
    )
    balance = next(
        (word for word in line if word.text.casefold() == "balance"),
        None,
    )

    if credit is None or debit is None or balance is None:
        return None

    return _ActivityColumns(
        credit_x=credit.x0,
        debit_x=debit.x0,
        balance_x=balance.x0,
    )


def _nearest_column(
    word: StatementWord,
    *,
    columns: _ActivityColumns,
) -> str:
    """Return the monetary column nearest a positioned amount."""
    center = (word.x0 + word.x1) / 2

    distances = {
        "credit": abs(center - columns.credit_x),
        "debit": abs(center - columns.debit_x),
        "balance": abs(center - columns.balance_x),
    }

    return min(distances, key=distances.__getitem__)


def _parse_transaction_line(
    words: Sequence[StatementWord],
    *,
    columns: _ActivityColumns,
) -> WellsFargoBusinessCheckingActivityRow | None:
    """Parse one business checking transaction line."""
    if _DATE_PATTERN.fullmatch(words[0].text) is None:
        return None

    monetary_words = tuple(
        word for word in words[1:] if _AMOUNT_PATTERN.fullmatch(word.text)
    )

    if not monetary_words:
        msg = (
            "Wells Fargo business checking transaction row contained no "
            f"monetary value: {_line_text(words)}"
        )
        raise ValueError(msg)

    amounts: dict[str, Decimal] = {}

    for word in monetary_words:
        column = _nearest_column(
            word,
            columns=columns,
        )

        if column in amounts:
            msg = (
                "Wells Fargo business checking transaction row contained "
                f"multiple values for the {column} column: {_line_text(words)}"
            )
            raise ValueError(msg)

        amounts[column] = _parse_amount(word.text)

    if "credit" in amounts and "debit" in amounts:
        msg = (
            "Wells Fargo business checking transaction row contained both "
            f"a credit and debit: {_line_text(words)}"
        )
        raise ValueError(msg)

    if "credit" not in amounts and "debit" not in amounts:
        msg = (
            "Wells Fargo business checking transaction row contained no "
            f"transaction amount: {_line_text(words)}"
        )
        raise ValueError(msg)

    monetary_ids = {id(word) for word in monetary_words}

    description = " ".join(
        word.text for word in words[1:] if id(word) not in monetary_ids
    )

    return WellsFargoBusinessCheckingActivityRow(
        transaction_date=words[0].text,
        description=description,
        credit=amounts.get("credit"),
        debit=amounts.get("debit"),
        balance=amounts.get("balance"),
    )


def _parse_page_rows(
    page: StatementPage,
) -> tuple[WellsFargoBusinessCheckingActivityRow, ...]:
    """Parse business checking activity from one page."""
    lines = _group_words_by_line(page.words)

    rows: list[WellsFargoBusinessCheckingActivityRow] = []
    in_activity = False
    columns: _ActivityColumns | None = None

    for line in lines:
        line_text = _line_text(line)

        if _TRANSACTION_HISTORY_PATTERN.search(line_text):
            in_activity = True
            columns = None
            continue

        if not in_activity:
            continue

        if line_text.startswith(_SECTION_END_PREFIXES):
            break

        discovered_columns = _find_columns(line)

        if discovered_columns is not None:
            columns = discovered_columns
            continue

        if columns is None:
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
                description=f"{previous.description} {line_text}".strip(),
            )

    return tuple(rows)


def parse_activity_rows(
    text: StatementText,
) -> tuple[WellsFargoBusinessCheckingActivityRow, ...]:
    """Parse Wells Fargo business checking transaction-history rows."""
    rows: list[WellsFargoBusinessCheckingActivityRow] = []

    for page in text.pages:
        rows.extend(_parse_page_rows(page))

    return tuple(rows)
