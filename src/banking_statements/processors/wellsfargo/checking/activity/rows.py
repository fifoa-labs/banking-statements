"""
src/banking_statements/processors/wellsfargo/checking/activity/rows.py

Layout-aware transaction-history row parsing for Wells Fargo
checking statements.
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
class WellsFargoCheckingActivityRow:
    """Normalized raw row from Wells Fargo checking transaction history."""

    transaction_date: str
    description: str
    addition: Decimal | None
    subtraction: Decimal | None
    balance: Decimal | None


@dataclass(frozen=True, slots=True)
class _ActivityColumns:
    """Horizontal anchors for Wells Fargo activity monetary columns."""

    addition_x: float
    subtraction_x: float
    balance_x: float


_DATE_PATTERN = re.compile(
    r"^\d{1,2}/\d{1,2}$",
)

_AMOUNT_PATTERN = re.compile(
    r"^-?[\d,]+\.\d{2}$",
)

_CHECKING_HEADING_PATTERN = re.compile(
    r"Wells\s+Far\s*go\s+.*Checking",
    re.IGNORECASE,
)

_SAVINGS_HEADING_PATTERN = re.compile(
    r"Wells\s+Far\s*go\s+.*Savings",
    re.IGNORECASE,
)

_TRANSACTION_HISTORY_PATTERN = re.compile(
    r"Transaction\s+hi\s*story",
    re.IGNORECASE,
)

_SECTION_END_PREFIXES = (
    "Monthly service fee summary",
    "Ending balance on ",
    "Ending bal ance on ",
    "Totals ",
)

_LINE_TOLERANCE = 3.0


def _parse_amount(value: str) -> Decimal:
    """Parse a Wells Fargo checking monetary amount."""
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


def _line_text(words: Sequence[StatementWord]) -> str:
    """Return visual line text from positioned words."""
    return " ".join(word.text for word in words)


def _find_activity_columns(
    lines: Sequence[Sequence[StatementWord]],
) -> tuple[int, _ActivityColumns] | None:
    """Locate an activity-table header and its monetary columns."""
    for index, line in enumerate(lines):
        additions = next(
            (word for word in line if word.text.casefold() == "additions"),
            None,
        )
        subtractions = next(
            (word for word in line if word.text.casefold() == "subtractions"),
            None,
        )
        balance = next(
            (word for word in line if word.text.casefold() == "balance"),
            None,
        )

        if additions is None or subtractions is None or balance is None:
            continue

        return (
            index,
            _ActivityColumns(
                addition_x=additions.x0,
                subtraction_x=subtractions.x0,
                balance_x=balance.x0,
            ),
        )

    return None


def _nearest_column(
    word: StatementWord,
    *,
    columns: _ActivityColumns,
) -> str:
    """Return the monetary column nearest a positioned amount."""
    center = (word.x0 + word.x1) / 2

    distances = {
        "addition": abs(center - columns.addition_x),
        "subtraction": abs(center - columns.subtraction_x),
        "balance": abs(center - columns.balance_x),
    }

    return min(distances, key=distances.__getitem__)


def _parse_transaction_line(
    words: Sequence[StatementWord],
    *,
    columns: _ActivityColumns,
) -> WellsFargoCheckingActivityRow | None:
    """Parse one visual transaction row."""
    if _DATE_PATTERN.fullmatch(words[0].text) is None:
        return None

    monetary_words = tuple(
        word for word in words[1:] if _AMOUNT_PATTERN.fullmatch(word.text)
    )

    if not monetary_words:
        msg = (
            "Wells Fargo checking transaction row contained no "
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
                "Wells Fargo checking transaction row contained multiple "
                f"values for the {column} column: {_line_text(words)}"
            )
            raise ValueError(msg)

        amounts[column] = _parse_amount(word.text)

    if "addition" in amounts and "subtraction" in amounts:
        msg = (
            "Wells Fargo checking transaction row contained both an "
            f"addition and subtraction: {_line_text(words)}"
        )
        raise ValueError(msg)

    if "addition" not in amounts and "subtraction" not in amounts:
        msg = (
            "Wells Fargo checking transaction row contained no transaction "
            f"amount: {_line_text(words)}"
        )
        raise ValueError(msg)

    monetary_ids = {id(word) for word in monetary_words}

    description_words = [
        word.text for word in words[1:] if id(word) not in monetary_ids
    ]

    return WellsFargoCheckingActivityRow(
        transaction_date=words[0].text,
        description=" ".join(description_words),
        addition=amounts.get("addition"),
        subtraction=amounts.get("subtraction"),
        balance=amounts.get("balance"),
    )


def _parse_page_activity(  # noqa: C901
    page: StatementPage,
    *,
    checking_active: bool,
) -> tuple[
    tuple[WellsFargoCheckingActivityRow, ...],
    bool,
]:
    """Parse Wells Fargo checking activity from one physical page."""
    lines = _group_words_by_line(page.words)

    if not lines:
        return (), checking_active

    rows: list[WellsFargoCheckingActivityRow] = []
    in_activity = False
    columns: _ActivityColumns | None = None

    for index, line in enumerate(lines):
        line_text = _line_text(line)

        if _CHECKING_HEADING_PATTERN.search(line_text):
            checking_active = True
            in_activity = False
            columns = None
            continue

        if _SAVINGS_HEADING_PATTERN.search(line_text):
            checking_active = False
            in_activity = False
            columns = None
            continue

        if not checking_active:
            continue

        if _TRANSACTION_HISTORY_PATTERN.search(line_text):
            in_activity = True
            columns = None
            continue

        if not in_activity:
            continue

        if line_text.startswith(_SECTION_END_PREFIXES):
            in_activity = False
            columns = None
            continue

        if columns is None:
            header = _find_activity_columns(lines[index : index + 1])

            if header is not None:
                _, columns = header

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

    return tuple(rows), checking_active


def parse_activity_rows(
    text: StatementText,
) -> tuple[WellsFargoCheckingActivityRow, ...]:
    """Parse layout-aware Wells Fargo checking transaction-history rows."""
    rows: list[WellsFargoCheckingActivityRow] = []
    checking_active = False

    for page in text.pages:
        page_rows, checking_active = _parse_page_activity(
            page,
            checking_active=checking_active,
        )
        rows.extend(page_rows)

    return tuple(rows)
