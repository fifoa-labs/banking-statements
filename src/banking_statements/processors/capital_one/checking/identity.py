"""
src/banking_statements/processors/capital_one/checking/identity.py

Identity parsing for supported Capital One 360 checking statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING

from banking_statements.domain import AccountIdentity, AccountType

if TYPE_CHECKING:
    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class CapitalOneCheckingIdentity:
    """Identity fields parsed from a Capital One 360 checking statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"^360 Checking - (?P<display>\d+)\b",
    re.MULTILINE,
)

_PERIOD_PATTERN = re.compile(
    r"STATEMENT PERIOD\s+"
    r"(?P<start>[A-Z][a-z]{2} \d{1,2})\s*-\s*"
    r"(?P<end>[A-Z][a-z]{2} \d{1,2}, \d{4})",
)


def _parse_month_day(value: str) -> tuple[int, int]:
    """Parse one abbreviated Capital One month/day value."""
    try:
        parsed = datetime.strptime(  # noqa: DTZ007
            f"{value} 2000",
            "%b %d %Y",
        )
    except ValueError as exc:
        msg = f"Invalid Capital One checking statement date: {value!r}."
        raise ValueError(msg) from exc

    return parsed.month, parsed.day


def _parse_end_date(value: str) -> date:
    """Parse the fully reported Capital One statement ending date."""
    try:
        return datetime.strptime(value, "%b %d, %Y").date()  # noqa: DTZ007
    except ValueError as exc:
        msg = f"Invalid Capital One checking statement date: {value!r}."
        raise ValueError(msg) from exc


def _resolve_start_date(
    value: str,
    *,
    statement_end: date,
) -> date:
    """Resolve an abbreviated start date against the statement end."""
    month, day = _parse_month_day(value)
    candidates: list[date] = []

    for year in (
        statement_end.year,
        statement_end.year - 1,
    ):
        try:
            candidate = date(
                year,
                month,
                day,
            )
        except ValueError:
            continue

        if candidate <= statement_end:
            candidates.append(candidate)

    if not candidates:
        msg = f"Invalid Capital One checking statement date: {value!r}."
        raise ValueError(msg)

    return max(candidates)


def parse_identity(text: StatementText) -> CapitalOneCheckingIdentity:
    """Parse Capital One checking account identity and statement period."""
    account_numbers = {
        match.group("display")
        for match in _ACCOUNT_PATTERN.finditer(text.text)
    }

    if len(account_numbers) != 1:
        msg = "Capital One checking account number was not found uniquely."
        raise ValueError(msg)

    period_values = {
        (
            match.group("start"),
            match.group("end"),
        )
        for match in _PERIOD_PATTERN.finditer(text.text)
    }

    if len(period_values) != 1:
        msg = "Capital One checking statement period was not found uniquely."
        raise ValueError(msg)

    start_text, end_text = next(iter(period_values))
    statement_end = _parse_end_date(end_text)
    statement_start = _resolve_start_date(
        start_text,
        statement_end=statement_end,
    )

    display_number = next(iter(account_numbers))

    return CapitalOneCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
