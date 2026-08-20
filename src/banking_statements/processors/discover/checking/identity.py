"""
src/banking_statements/processors/discover/checking/identity.py

Identity parsing for Discover checking statements.
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
class DiscoverCheckingIdentity:
    """Identity fields parsed from a Discover checking statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_FULL_ACCOUNT_PATTERN = re.compile(
    r"Account Number:\s*(?P<display>\d{10})\b",
)

_ENDING_ACCOUNT_PATTERN = re.compile(
    r"Account number\s*ending in\s*(?P<last4>\d{4})\b",
    re.IGNORECASE,
)

_PERIOD_PATTERN = re.compile(
    r"Statement Period:\s*"
    r"(?P<start>[A-Z][a-z]{2} \d{2}, \d{4})\s*-\s*"
    r"(?P<end>[A-Z][a-z]{2} \d{2}, \d{4})",
)


def _parse_date(value: str) -> date:
    """Parse a Discover statement-period date."""
    return datetime.strptime(value, "%b %d, %Y").date()  # noqa: DTZ007


def parse_identity(text: StatementText) -> DiscoverCheckingIdentity:
    """Parse account identity and statement period."""
    full_text = text.text

    full_match = _FULL_ACCOUNT_PATTERN.search(full_text)
    ending_matches = {
        match.group("last4")
        for match in _ENDING_ACCOUNT_PATTERN.finditer(full_text)
    }

    if full_match is not None:
        display_number = full_match.group("display")
        last4 = display_number[-4:]

        if ending_matches and ending_matches != {last4}:
            msg = "Discover checking account numbers do not agree."
            raise ValueError(msg)
    elif len(ending_matches) == 1:
        last4 = next(iter(ending_matches))
        display_number = last4
    else:
        msg = "Discover checking account number was not found uniquely."
        raise ValueError(msg)

    period_match = _PERIOD_PATTERN.search(full_text)
    if period_match is None:
        msg = "Discover checking statement period was not found."
        raise ValueError(msg)

    statement_start = _parse_date(period_match.group("start"))
    statement_end = _parse_date(period_match.group("end"))

    if statement_start > statement_end:
        msg = "Discover checking statement period starts after it ends."
        raise ValueError(msg)

    return DiscoverCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=display_number,
            last4=last4,
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
