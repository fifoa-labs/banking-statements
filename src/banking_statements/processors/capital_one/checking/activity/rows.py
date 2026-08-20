"""
src/banking_statements/processors/capital_one/checking/activity/rows.py

Logical activity-row reconstruction for Capital One 360 checking statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class CapitalOneCheckingActivitySection(StrEnum):
    """Economic directions reported by Capital One checking statements."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class CapitalOneCheckingActivityRow:
    """One reconstructed Capital One checking activity row."""

    transaction_date: str
    description: str
    amount: Decimal
    balance: Decimal
    section: CapitalOneCheckingActivitySection
    raw_text: str


_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
_AMOUNT = r"[\d,]+\.\d{2}"
_BALANCE = rf"(?P<balance>-?\${_AMOUNT})"

_TABLE_HEADER = "DATE DESCRIPTION CATEGORY AMOUNT BALANCE"

_FULL_ROW_PATTERN = re.compile(
    rf"^(?P<date>{_MONTH} \d{{1,2}})\s+"
    rf"(?P<description>.+?)\s+"
    rf"(?P<category>Credit|Debit)\s+"
    rf"(?P<sign>[+-])\s+"
    rf"\$(?P<amount>{_AMOUNT})\s+"
    rf"{_BALANCE}$",
)

_WRAPPED_ROW_PATTERN = re.compile(
    rf"^(?P<date>{_MONTH} \d{{1,2}})\s+"
    rf"(?P<category>Credit|Debit)\s+"
    rf"(?P<sign>[+-])\s+"
    rf"\$(?P<amount>{_AMOUNT})\s+"
    rf"{_BALANCE}$",
)

_OPENING_BALANCE_PATTERN = re.compile(
    rf"^{_MONTH} \d{{1,2}} Opening Balance "
    rf"(?P<amount>-?\${_AMOUNT})$",
    re.MULTILINE,
)

_CLOSING_BALANCE_PATTERN = re.compile(
    rf"^{_MONTH} \d{{1,2}} Closing Balance "
    rf"(?P<amount>-?\${_AMOUNT})$",
    re.MULTILINE,
)

_DATE_PREFIX_PATTERN = re.compile(
    rf"^{_MONTH} \d{{1,2}}\b",
)

_REFERENCE_PATTERN = re.compile(
    r"^[A-Z0-9]{15}$",
)


def _parse_amount(value: str) -> Decimal:
    """Parse one Capital One checking monetary amount."""
    return Decimal(value.replace("$", "").replace(",", ""))


def _section(
    category: str,
    sign: str,
) -> CapitalOneCheckingActivitySection:
    """Validate and normalize the statement-reported transaction direction."""
    if category == "Credit" and sign == "+":
        return CapitalOneCheckingActivitySection.CREDIT

    if category == "Debit" and sign == "-":
        return CapitalOneCheckingActivitySection.DEBIT

    msg = (
        "Capital One checking transaction category and sign do not agree: "
        f"{category} {sign}"
    )
    raise ValueError(msg)


def _append_continuation(
    row: CapitalOneCheckingActivityRow,
    lines: list[str],
) -> CapitalOneCheckingActivityRow:
    """Append logical description continuation lines to one activity row."""
    detail = " ".join(lines)

    return replace(
        row,
        description=f"{row.description} {detail}".strip(),
        raw_text="\n".join((row.raw_text, *lines)),
    )


def _append_raw_evidence(
    row: CapitalOneCheckingActivityRow,
    line: str,
) -> CapitalOneCheckingActivityRow:
    """Append evidence-only detail without changing the description."""
    return replace(
        row,
        raw_text=f"{row.raw_text}\n{line}",
    )


def _parse_boundary_balance(
    text: str,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> Decimal:
    """Parse one uniquely reported activity boundary balance."""
    values = {
        _parse_amount(match.group("amount"))
        for match in pattern.finditer(text)
    }

    if len(values) != 1:
        msg = f"Capital One checking activity {field} was not found uniquely."
        raise ValueError(msg)

    return next(iter(values))


def _finish_pending(
    rows: list[CapitalOneCheckingActivityRow],
    pending: list[str],
) -> None:
    """Attach unresolved continuation text to the preceding transaction."""
    if not pending:
        return

    if not rows:
        msg = (
            "Capital One checking activity contained orphan continuation "
            f"text: {' '.join(pending)}"
        )
        raise ValueError(msg)

    rows[-1] = _append_continuation(
        rows[-1],
        pending,
    )
    pending.clear()


def _build_full_row(
    match: re.Match[str],
    *,
    raw_text: str,
) -> CapitalOneCheckingActivityRow:
    """Build one complete single-line Capital One checking row."""
    return CapitalOneCheckingActivityRow(
        transaction_date=match.group("date"),
        description=match.group("description"),
        amount=_parse_amount(match.group("amount")),
        balance=_parse_amount(match.group("balance")),
        section=_section(
            match.group("category"),
            match.group("sign"),
        ),
        raw_text=raw_text,
    )


def _build_wrapped_row(
    match: re.Match[str],
    *,
    description_lines: list[str],
    raw_text: str,
) -> CapitalOneCheckingActivityRow:
    """Build one row whose description precedes the dated amount line."""
    if not description_lines:
        msg = (
            "Capital One checking wrapped transaction row did not have "
            "a description."
        )
        raise ValueError(msg)

    return CapitalOneCheckingActivityRow(
        transaction_date=match.group("date"),
        description=" ".join(description_lines),
        amount=_parse_amount(match.group("amount")),
        balance=_parse_amount(match.group("balance")),
        section=_section(
            match.group("category"),
            match.group("sign"),
        ),
        raw_text=raw_text,
    )


def _validate_running_balances(
    rows: list[CapitalOneCheckingActivityRow],
    *,
    opening_balance: Decimal,
    closing_balance: Decimal,
) -> None:
    """Require every parsed row to agree with the reported running balance."""
    running_balance = opening_balance

    for row in rows:
        if row.section is CapitalOneCheckingActivitySection.CREDIT:
            running_balance += row.amount
        else:
            running_balance -= row.amount

        if running_balance != row.balance:
            msg = (
                "Capital One checking transaction does not reconcile with "
                f"its running balance: {row.raw_text}"
            )
            raise ValueError(msg)

    if running_balance != closing_balance:
        msg = (
            "Capital One checking parsed activity does not reconcile with "
            "the reported closing balance."
        )
        raise ValueError(msg)


def parse_activity_rows(  # noqa: C901
    text: StatementText,
) -> tuple[CapitalOneCheckingActivityRow, ...]:
    """Parse Capital One checking activity across the proven 360 layout."""
    opening_balance = _parse_boundary_balance(
        text.text,
        field="opening balance",
        pattern=_OPENING_BALANCE_PATTERN,
    )
    closing_balance = _parse_boundary_balance(
        text.text,
        field="closing balance",
        pattern=_CLOSING_BALANCE_PATTERN,
    )

    rows: list[CapitalOneCheckingActivityRow] = []
    pending: list[str] = []
    in_table = False
    last_row_index: int | None = None

    for raw_line in text.text.splitlines():
        line = raw_line.strip()

        if line == _TABLE_HEADER:
            _finish_pending(rows, pending)
            in_table = True
            last_row_index = None
            continue

        if not in_table:
            continue

        if line == "Fees Summary" or line.startswith(
            ("Page ", "capitalone.com")
        ):
            _finish_pending(rows, pending)
            in_table = False
            last_row_index = None
            continue

        if not line:
            continue

        if _OPENING_BALANCE_PATTERN.fullmatch(line) is not None:
            continue

        if _CLOSING_BALANCE_PATTERN.fullmatch(line) is not None:
            _finish_pending(rows, pending)
            continue

        full_match = _FULL_ROW_PATTERN.fullmatch(line)

        if full_match is not None:
            _finish_pending(rows, pending)
            rows.append(
                _build_full_row(
                    full_match,
                    raw_text=line,
                )
            )
            last_row_index = len(rows) - 1
            continue

        wrapped_match = _WRAPPED_ROW_PATTERN.fullmatch(line)

        if wrapped_match is not None:
            raw_text = "\n".join((*pending, line))
            rows.append(
                _build_wrapped_row(
                    wrapped_match,
                    description_lines=pending,
                    raw_text=raw_text,
                )
            )
            pending.clear()
            last_row_index = len(rows) - 1
            continue

        if _DATE_PREFIX_PATTERN.match(line):
            msg = f"Unrecognized Capital One checking transaction row: {line}"
            raise ValueError(msg)

        if (
            last_row_index is not None
            and not pending
            and _REFERENCE_PATTERN.fullmatch(line) is not None
        ):
            rows[last_row_index] = _append_raw_evidence(
                rows[last_row_index],
                line,
            )
            continue

        pending.append(line)

    _finish_pending(rows, pending)

    _validate_running_balances(
        rows,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
    )

    return tuple(rows)
