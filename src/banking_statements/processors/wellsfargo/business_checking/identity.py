"""
src/banking_statements/processors/wellsfargo/business_checking/identity.py

Identity parsing for supported Wells Fargo business checking statements.
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
class WellsFargoBusinessCheckingIdentity:
    """Identity fields parsed from a Wells Fargo
    business checking statement.
    """

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Statement period activity summary\s+"
    r"Account number:\s*(?P<display>\d+)",
    re.IGNORECASE,
)

_FEE_PERIOD_PATTERN = re.compile(
    r"Fee period\s+"
    r"(?P<start>\d{2}/\d{2}/\d{4})"
    r"\s+-\s+"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
)


def _parse_date(value: str) -> date:
    """Parse a Wells Fargo business checking statement date."""
    return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007


def parse_identity(
    text: StatementText,
) -> WellsFargoBusinessCheckingIdentity:
    """Parse identity fields from a Wells Fargo business checking statement."""
    full_text = text.text

    account_match = _ACCOUNT_PATTERN.search(full_text)
    if account_match is None:
        msg = "Wells Fargo business checking account number was not found."
        raise ValueError(msg)

    period_match = _FEE_PERIOD_PATTERN.search(full_text)
    if period_match is None:
        msg = "Wells Fargo business checking statement period was not found."
        raise ValueError(msg)

    display_number = account_match.group("display")

    return WellsFargoBusinessCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=_parse_date(period_match.group("start")),
        statement_end=_parse_date(period_match.group("end")),
    )
