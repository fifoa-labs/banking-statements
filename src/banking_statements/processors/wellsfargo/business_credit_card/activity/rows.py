"""
src/banking_statements/processors/wellsfargo/business_credit_card/activity/rows.py

Layout-aware activity parsing for Wells Fargo business credit-card statements.
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
class WellsFargoBusinessCreditCardActivityRow:
    """One normalized Wells Fargo business credit-card activity row."""

    transaction_date: str
    post_date: str
    reference_number: str
    description: str
    credit: Decimal | None
    charge: Decimal | None


@dataclass(frozen=True, slots=True)
class _ActivityColumns:
    """Horizontal anchors for business credit-card monetary columns."""

    credit_x: float
    charge_x: float


_DATE_PATTERN = re.compile(
    r"^\d{2}/\d{2}$",
)

_AMOUNT_PATTERN = re.compile(
    r"^-?[\d,]+\.\d{2}$",
)

_TRANSACTION_DETAILS_PATTERN = re.compile(
    r"^Transaction Details$",
    re.IGNORECASE,
)

_LINE_TOLERANCE = 3.0

_IGNORED_PREFIXES = (
    "Trans Post Reference",
    "TOTAL ",
    "Transaction Summary For ",
    "Sub Account Number Ending In ",
    "Summary of Sub Account Usage",
    "Sub Account Monthly Spend",
    "Name Number Ending In",
    "Rate Information",
    "The transactions detailed on ",
)


def _parse_amount(value: str) -> Decimal:
    """Parse a Wells Fargo business credit-card amount."""
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


def _line_text(
    words: Sequence[StatementWord],
) -> str:
    """Return reconstructed visual-line text."""
    return " ".join(word.text for word in words)


def _find_columns(
    line: Sequence[StatementWord],
) -> _ActivityColumns | None:
    """Locate Credits and Charges activity-column anchors."""
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


def _nearest_column(
    word: StatementWord,
    *,
    columns: _ActivityColumns,
) -> str:
    """Return the monetary column nearest the positioned amount."""
    center = (word.x0 + word.x1) / 2

    credit_distance = abs(center - columns.credit_x)
    charge_distance = abs(center - columns.charge_x)

    return "credit" if credit_distance < charge_distance else "charge"


def _parse_transaction_line(
    words: Sequence[StatementWord],
    *,
    columns: _ActivityColumns,
) -> WellsFargoBusinessCreditCardActivityRow | None:
    """Parse one Wells Fargo business credit-card transaction line."""
    if len(words) < 4:  # noqa: PLR2004
        return None

    if _DATE_PATTERN.fullmatch(words[0].text) is None:
        return None

    if _DATE_PATTERN.fullmatch(words[1].text) is None:
        return None

    amount_words = tuple(
        word
        for word in words[3:]
        if _AMOUNT_PATTERN.fullmatch(word.text)
        and word.x0 >= columns.credit_x - 20
    )

    if len(amount_words) != 1:
        msg = (
            "Wells Fargo business credit-card transaction row must contain "
            f"exactly one credit or charge amount: {_line_text(words)}"
        )
        raise ValueError(msg)

    amount_word = amount_words[0]

    column = _nearest_column(
        amount_word,
        columns=columns,
    )

    amount = _parse_amount(amount_word.text)

    description = " ".join(
        word.text for word in words[3:] if word is not amount_word
    )

    return WellsFargoBusinessCreditCardActivityRow(
        transaction_date=words[0].text,
        post_date=words[1].text,
        reference_number=words[2].text,
        description=description,
        credit=amount if column == "credit" else None,
        charge=amount if column == "charge" else None,
    )


def _is_ignored_structure(line_text: str) -> bool:
    """Return whether a visual line is business-card structure."""
    return line_text.startswith(_IGNORED_PREFIXES) or (
        "Sub Acct Ending In" in line_text
    )


def _parse_page_rows(
    page: StatementPage,
) -> tuple[WellsFargoBusinessCreditCardActivityRow, ...]:
    """Parse business credit-card activity from one page."""
    lines = _group_words_by_line(page.words)

    rows: list[WellsFargoBusinessCreditCardActivityRow] = []
    in_activity = False
    columns: _ActivityColumns | None = None

    for line in lines:
        line_text = _line_text(line)

        if _TRANSACTION_DETAILS_PATTERN.match(line_text):
            in_activity = True
            columns = None
            continue

        if not in_activity:
            continue

        discovered_columns = _find_columns(line)

        if discovered_columns is not None:
            columns = discovered_columns
            continue

        if columns is None:
            continue

        if _is_ignored_structure(line_text):
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
) -> tuple[WellsFargoBusinessCreditCardActivityRow, ...]:
    """Parse Wells Fargo business credit-card activity rows."""
    rows: list[WellsFargoBusinessCreditCardActivityRow] = []

    for page in text.pages:
        rows.extend(_parse_page_rows(page))

    return tuple(rows)
