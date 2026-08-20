"""
src/banking_statements/processors/american_express/business_checking/identity.py

Identity parsing for American Express business-checking statements.
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
class AmericanExpressBusinessCheckingIdentity:
    """Identity fields parsed from an American Express business statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERNS = (
    re.compile(
        r"AccountEnding\s+\*(?P<last4>\d{4})",
    ),
    re.compile(
        r"Account Ending:\s*\*\s*(?P<last4>\d{4})",
    ),
)


_PERIOD_PATTERNS = (
    re.compile(
        r"StatementPeriod\s+"
        r"(?P<start>\d{2}/\d{2}/\d{4})\s*-\s*"
        r"(?P<end>\d{2}/\d{2}/\d{4})",
    ),
    re.compile(
        r"Beginning Balance as of\s+"
        r"(?P<start>\d{2}/\d{2}/\d{4})\s+"
        r"\$[\d,]+\.\d{2}"
        r".*?"
        r"Ending Balance as of\s+"
        r"(?P<end>\d{2}/\d{2}/\d{4})",
        re.DOTALL,
    ),
)


def _parse_date(value: str) -> date:
    """Parse an American Express business-checking statement date."""
    return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007


def parse_identity(
    text: StatementText,
) -> AmericanExpressBusinessCheckingIdentity:
    """Parse identity fields from an American Express business statement."""
    full_text = text.text

    account_match = next(
        (
            match
            for pattern in _ACCOUNT_PATTERNS
            if (match := pattern.search(full_text)) is not None
        ),
        None,
    )
    if account_match is None:
        msg = (
            "American Express business-checking account ending was not found."
        )
        raise ValueError(msg)

    period_match = next(
        (
            match
            for pattern in _PERIOD_PATTERNS
            if (match := pattern.search(full_text)) is not None
        ),
        None,
    )
    if period_match is None:
        msg = (
            "American Express business-checking statement period was not "
            "found."
        )
        raise ValueError(msg)

    last4 = account_match.group("last4")

    return AmericanExpressBusinessCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=last4,
            last4=last4,
        ),
        statement_start=_parse_date(period_match.group("start")),
        statement_end=_parse_date(period_match.group("end")),
    )
