"""
src/banking_statements/processors/discover/credit_card/identity.py

Identity parsing for Discover credit-card statements.
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
class DiscoverCreditCardIdentity:
    """Identity fields parsed from a Discover credit-card statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_ENDING_PATTERNS = (
    re.compile(
        r"Account number ending in\s*(?P<last4>\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"DISCOVER IT® CARD ENDING IN\s*(?P<last4>\d{4})\b",
        re.IGNORECASE,
    ),
)

_LEGACY_PERIOD_PATTERN = re.compile(
    r"Open Date:\s*"
    r"(?P<start>[A-Z][a-z]{2} \d{1,2}, \d{4})"
    r"\s*-\s*"
    r"Close Date:\s*"
    r"(?P<end>[A-Z][a-z]{2} \d{1,2}, \d{4})",
    re.IGNORECASE,
)

_CURRENT_PERIOD_PATTERN = re.compile(
    r"(?:Account\s*Summary|OPEN TO CLOSE DATE:)\s*"
    r"(?P<start>\d{2}/\d{2}/\d{4})"
    r"\s*-\s*"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)


def _parse_date(value: str) -> date:
    """Parse one Discover credit-card statement-period date."""
    date_format = "%m/%d/%Y" if "/" in value else "%b %d, %Y"
    return datetime.strptime(value, date_format).date()  # noqa: DTZ007


def _parse_statement_period(text: str) -> tuple[date, date]:
    """Parse the first supported Discover credit-card statement period."""
    period_match = _LEGACY_PERIOD_PATTERN.search(text)

    if period_match is None:
        period_match = _CURRENT_PERIOD_PATTERN.search(text)

    if period_match is None:
        msg = "Discover credit-card statement period was not found."
        raise ValueError(msg)

    statement_start = _parse_date(period_match.group("start"))
    statement_end = _parse_date(period_match.group("end"))

    if statement_start > statement_end:
        msg = "Discover credit-card statement period starts after it ends."
        raise ValueError(msg)

    return statement_start, statement_end


def parse_identity(text: StatementText) -> DiscoverCreditCardIdentity:
    """Parse Discover credit-card account identity and statement period."""
    account_endings = {
        match.group("last4")
        for pattern in _ACCOUNT_ENDING_PATTERNS
        for match in pattern.finditer(text.text)
    }

    if len(account_endings) != 1:
        msg = "Discover credit-card account ending was not found uniquely."
        raise ValueError(msg)

    last4 = next(iter(account_endings))
    statement_start, statement_end = _parse_statement_period(text.text)

    return DiscoverCreditCardIdentity(
        account=AccountIdentity(
            account_type=AccountType.CREDIT_CARD,
            display_number=last4,
            last4=last4,
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
