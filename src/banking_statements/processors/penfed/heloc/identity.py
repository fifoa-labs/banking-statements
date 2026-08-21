"""
src/banking_statements/processors/penfed/heloc/identity.py

Identity parsing for supported PenFed HELOC statements.
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
class PenFedHelocIdentity:
    """Identity fields parsed from a PenFed HELOC statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERNS = (
    re.compile(r"Loan Number\s+(?P<account>\d{6,})\b"),
    re.compile(r"Account Number:\s*(?P<account>\d{6,})\b"),
)

_CLOSING_DATE_PATTERN = re.compile(
    r"Statement Closing Date:\s*"
    r"(?P<date>"
    r"[A-Z][a-z]+ \d{1,2}, \d{4}"
    r"|"
    r"\d{2}/\d{2}/\d{4}"
    r")",
)

_PERIOD_PATTERN = re.compile(
    r"Transaction Activity \("
    r"(?P<start>\d{2}/\d{2}/\d{2})"
    r"\s+through\s+"
    r"(?P<end>\d{2}/\d{2}/\d{2})"
    r"\)",
)


def _parse_closing_date(value: str) -> date:
    """Parse a PenFed statement closing date."""
    date_format = "%m/%d/%Y" if "/" in value else "%B %d, %Y"
    return datetime.strptime(value, date_format).date()  # noqa: DTZ007


def _parse_short_date(value: str) -> date:
    """Parse a PenFed activity-period date."""
    return datetime.strptime(value, "%m/%d/%y").date()  # noqa: DTZ007


def parse_identity(text: StatementText) -> PenFedHelocIdentity:
    """Parse PenFed HELOC account identity and statement period."""
    account_numbers = {
        match.group("account")
        for pattern in _ACCOUNT_PATTERNS
        for match in pattern.finditer(text.text)
    }

    if len(account_numbers) != 1:
        msg = "PenFed HELOC account number was not found uniquely."
        raise ValueError(msg)

    closing_dates = {
        _parse_closing_date(match.group("date"))
        for match in _CLOSING_DATE_PATTERN.finditer(text.text)
    }

    if len(closing_dates) != 1:
        msg = "PenFed HELOC statement closing date was not found uniquely."
        raise ValueError(msg)

    periods = {
        (
            _parse_short_date(match.group("start")),
            _parse_short_date(match.group("end")),
        )
        for match in _PERIOD_PATTERN.finditer(text.text)
    }

    if len(periods) != 1:
        msg = (
            "PenFed HELOC transaction activity period was not found uniquely."
        )
        raise ValueError(msg)

    statement_start, statement_end = next(iter(periods))
    closing_date = next(iter(closing_dates))

    if statement_start > statement_end:
        msg = "PenFed HELOC statement period starts after it ends."
        raise ValueError(msg)

    if statement_end != closing_date:
        msg = (
            "PenFed HELOC statement closing date does not match the "
            "transaction activity period end."
        )
        raise ValueError(msg)

    display_number = next(iter(account_numbers))

    return PenFedHelocIdentity(
        account=AccountIdentity(
            account_type=AccountType.LINE_OF_CREDIT,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
