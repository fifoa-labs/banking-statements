"""
src/banking_statements/processors/chase/checking/identity.py

Identity parsing for Chase checking statements.
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
class ChaseCheckingIdentity:
    """Identity fields parsed from a Chase checking statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Account Number:\s*(?P<display>\d+)",
)

_PERIOD_PATTERN = re.compile(
    r"(?P<start>[A-Z][a-z]+ \d{1,2}, \d{4})\s+through\s+"
    r"(?P<end>[A-Z][a-z]+ \d{1,2}, \d{4})",
)


def _parse_date(value: str) -> date:
    """Parse a Chase checking statement date."""
    return datetime.strptime(value, "%B %d, %Y").date()  # noqa: DTZ007


def parse_identity(text: StatementText) -> ChaseCheckingIdentity:
    """Parse identity fields from a Chase checking statement."""
    full_text = text.text

    account_match = _ACCOUNT_PATTERN.search(full_text)
    if account_match is None:
        msg = "Chase checking account number was not found."
        raise ValueError(msg)

    period_match = _PERIOD_PATTERN.search(full_text)
    if period_match is None:
        msg = "Chase checking statement period was not found."
        raise ValueError(msg)

    display_number = account_match.group("display")

    return ChaseCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=_parse_date(period_match.group("start")),
        statement_end=_parse_date(period_match.group("end")),
    )
