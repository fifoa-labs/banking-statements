"""
src/banking_statements/processors/chase/heloc/identity.py

Identity parsing for Chase home-equity line-of-credit statements.
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
class ChaseHelocIdentity:
    """Identity fields parsed from a Chase HELOC statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Account number\s+(?P<display>\d{6,})",
    re.IGNORECASE,
)

_PERIOD_PATTERN = re.compile(
    r"Statement Period\s+"
    r"(?P<start>\d{2}/\d{2}/\d{4})\s*-\s*"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)

_UNLABELED_PERIOD_PATTERN = re.compile(
    r"(?P<start>\d{2}/\d{2}/\d{4})\s*-\s*"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
)


def _parse_date(value: str) -> date:
    """Parse a Chase HELOC statement date."""
    return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007


def parse_identity(text: StatementText) -> ChaseHelocIdentity:
    """Parse identity fields from a Chase HELOC statement."""
    full_text = text.text

    account_match = _ACCOUNT_PATTERN.search(full_text)
    if account_match is None:
        msg = "Chase HELOC account number was not found."
        raise ValueError(msg)

    period_match = _PERIOD_PATTERN.search(full_text)

    if period_match is None:
        fallback_matches = tuple(_UNLABELED_PERIOD_PATTERN.finditer(full_text))
        unique_periods = {
            (
                match.group("start"),
                match.group("end"),
            ): match
            for match in fallback_matches
        }

        if len(unique_periods) != 1:
            msg = "Chase HELOC statement period was not found uniquely."
            raise ValueError(msg)

        period_match = next(iter(unique_periods.values()))

    statement_start = _parse_date(period_match.group("start"))
    statement_end = _parse_date(period_match.group("end"))

    if statement_start > statement_end:
        msg = "Chase HELOC statement period starts after it ends."
        raise ValueError(msg)

    display_number = account_match.group("display")

    return ChaseHelocIdentity(
        account=AccountIdentity(
            account_type=AccountType.LINE_OF_CREDIT,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
