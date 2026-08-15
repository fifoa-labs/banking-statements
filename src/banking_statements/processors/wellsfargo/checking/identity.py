"""
src/banking_statements/processors/wellsfargo/checking/identity.py

Identity parsing for supported Wells Fargo checking statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING

from banking_statements.domain import AccountIdentity, AccountType

from .sections import extract_checking_section

if TYPE_CHECKING:
    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class WellsFargoCheckingIdentity:
    """Identity fields parsed from a Wells Fargo checking statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"(?:Statement\s+p\s*eriod\s+)?"
    r"activity\s+sum\s*mary\s+"
    r"Account number:\s*(?P<display>\d+)",
    re.IGNORECASE,
)

_FEE_PERIOD_PATTERN = re.compile(
    r"Fee period\s+"
    r"(?P<start>\d{1,2}/\d{1,2}/\d{4})"
    r"\s+-\s+"
    r"(?P<end>\d{1,2}/\d{1,2}/\d{4})",
)

_STATEMENT_END_PATTERN = re.compile(
    r"(?P<end>[A-Z][a-z]+ \d{1,2}, \d{4})\s+Page\s+\d+\s+of\s+\d+",
)

_BEGINNING_BALANCE_DATE_PATTERN = re.compile(
    r"Beginning\s+b\s*alance\s+on\s+"
    r"(?P<month>\d{1,2})/(?P<day>\d{1,2})",
)


def _parse_numeric_date(value: str) -> date:
    """Parse a numeric Wells Fargo statement date."""
    return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007


def _parse_named_date(value: str) -> date:
    """Parse a named Wells Fargo statement date."""
    return datetime.strptime(value, "%B %d, %Y").date()  # noqa: DTZ007


def _resolve_start_date(
    *,
    month: int,
    day: int,
    statement_end: date,
) -> date:
    """Resolve an M/D start date relative to the statement ending date."""
    year = statement_end.year

    candidate = date(year, month, day)

    if candidate > statement_end:
        candidate = date(year - 1, month, day)

    return candidate


def _parse_statement_period(
    text: StatementText,
    *,
    section: str,
) -> tuple[date, date]:
    """Parse the Wells Fargo checking statement period."""
    fee_period_match = _FEE_PERIOD_PATTERN.search(section)

    if fee_period_match is not None:
        return (
            _parse_numeric_date(fee_period_match.group("start")),
            _parse_numeric_date(fee_period_match.group("end")),
        )

    statement_end_match = _STATEMENT_END_PATTERN.search(text.text)
    beginning_match = _BEGINNING_BALANCE_DATE_PATTERN.search(section)

    if statement_end_match is None or beginning_match is None:
        msg = "Wells Fargo checking statement period was not found."
        raise ValueError(msg)

    statement_end = _parse_named_date(
        statement_end_match.group("end"),
    )

    statement_start = _resolve_start_date(
        month=int(beginning_match.group("month")),
        day=int(beginning_match.group("day")),
        statement_end=statement_end,
    )

    return statement_start, statement_end


def parse_identity(text: StatementText) -> WellsFargoCheckingIdentity:
    """Parse identity fields from a Wells Fargo checking statement."""
    section = extract_checking_section(text)

    account_match = _ACCOUNT_PATTERN.search(section)
    if account_match is None:
        msg = "Wells Fargo checking account number was not found."
        raise ValueError(msg)

    statement_start, statement_end = _parse_statement_period(
        text,
        section=section,
    )

    display_number = account_match.group("display")

    return WellsFargoCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
