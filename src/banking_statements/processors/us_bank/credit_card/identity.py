"""
src/banking_statements/processors/us_bank/credit_card/identity.py

Identity parsing for supported U.S. Bank credit-card statements.
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
class USBankCreditCardIdentity:
    """Identity fields parsed from a U.S. Bank credit-card statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERNS = (
    re.compile(
        r"Account Number:\s*"
        r"(?P<display>(?:\d{4}|#{4})\s+"
        r"(?:\d{4}|#{4})\s+(?:\d{4}|#{4})\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"Account Ending in:\s*"
        r"(?P<display>#{4}\s+#{4}\s+#{4}\s+\d{4})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bAccount:\s*"
        r"(?P<display>(?:\d{4}|#{4})\s+"
        r"(?:\d{4}|#{4})\s+(?:\d{4}|#{4})\s+\d{4})",
        re.IGNORECASE,
    ),
)

_PERIOD_PATTERN = re.compile(
    r"(?P<start>\d{2}/\d{2}/\d{4})\s*-\s*"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
)


def _parse_date(value: str) -> date:
    """Parse one U.S. Bank credit-card statement date."""
    try:
        return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007
    except ValueError as exc:
        msg = f"Invalid U.S. Bank credit-card statement date: {value!r}."
        raise ValueError(msg) from exc


def _last4(display: str) -> str:
    """Return the final four digits from a U.S. Bank account display."""
    digits = re.sub(r"\D", "", display)
    if len(digits) < 4:  # noqa: PLR2004
        msg = "U.S. Bank credit-card account ending was not found."
        raise ValueError(msg)
    return digits[-4:]


def parse_identity(text: StatementText) -> USBankCreditCardIdentity:
    """Parse U.S. Bank credit-card account identity and statement period."""
    account_matches = [
        match.group("display")
        for pattern in _ACCOUNT_PATTERNS
        for match in pattern.finditer(text.text)
    ]
    account_endings = {_last4(display) for display in account_matches}

    if len(account_endings) != 1 or not account_matches:
        msg = "U.S. Bank credit-card account ending was not found uniquely."
        raise ValueError(msg)

    last4 = next(iter(account_endings))
    display_number = next(
        display for display in account_matches if _last4(display) == last4
    )

    periods = {
        (match.group("start"), match.group("end"))
        for match in _PERIOD_PATTERN.finditer(text.text)
    }
    if len(periods) != 1:
        msg = "U.S. Bank credit-card statement period was not found uniquely."
        raise ValueError(msg)

    start_text, end_text = next(iter(periods))
    statement_start = _parse_date(start_text)
    statement_end = _parse_date(end_text)

    if statement_start > statement_end:
        msg = "U.S. Bank credit-card statement period starts after it ends."
        raise ValueError(msg)

    return USBankCreditCardIdentity(
        account=AccountIdentity(
            account_type=AccountType.CREDIT_CARD,
            display_number=display_number,
            last4=last4,
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
