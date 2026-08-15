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

_PERIOD_PATTERN = re.compile(
    r"Fee period\s+"
    r"(?P<start>\d{1,2}/\d{1,2}/\d{4})"
    r"\s+-\s+"
    r"(?P<end>\d{1,2}/\d{1,2}/\d{4})",
)


def _parse_date(value: str) -> date:
    """Parse a Wells Fargo checking statement date."""
    return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007


def parse_identity(text: StatementText) -> WellsFargoCheckingIdentity:
    """Parse identity fields from a Wells Fargo checking statement."""
    section = extract_checking_section(text)

    account_match = _ACCOUNT_PATTERN.search(section)
    if account_match is None:
        msg = "Wells Fargo checking account number was not found."
        raise ValueError(msg)

    period_match = _PERIOD_PATTERN.search(section)
    if period_match is None:
        msg = "Wells Fargo checking statement period was not found."
        raise ValueError(msg)

    display_number = account_match.group("display")

    return WellsFargoCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=_parse_date(period_match.group("start")),
        statement_end=_parse_date(period_match.group("end")),
    )
