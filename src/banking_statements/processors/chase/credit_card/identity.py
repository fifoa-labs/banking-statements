"""
src/banking_statements/processors/chase/credit_card/identity.py

Identity parsing for Chase credit-card statements.
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
class ChaseCreditCardIdentity:
    """Identity fields parsed from a Chase credit-card statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date
    statement_date: date


_ACCOUNT_PATTERN = re.compile(
    r"Account [Nn]umber:\s+"
    r"(?P<display>"
    r"(?:XXXX XXXX XXXX|\d{4} \d{4} \d{4}) "
    r"(?P<last4>\d{4})"
    r")",
)

_UNLABELED_ACCOUNT_PATTERN = re.compile(
    r"\b(?P<display>"
    r"\d{4} \d{4} \d{4} (?P<last4>\d{4})"
    r")\b",
)

_PERIOD_PATTERN = re.compile(
    r"pening/Closing Date\s+"
    r"(?P<start>\d{2}/\d{2}/\d{2})\s*-\s*"
    r"(?P<end>\d{2}/\d{2}/\d{2})",
)

_STATEMENT_DATE_PATTERN = re.compile(
    r"Statement Date:\s*(?P<date>\d{2}/\d{2}/\d{2})",
)


def _parse_date(value: str) -> date:
    """Parse a Chase statement date."""
    return datetime.strptime(value, "%m/%d/%y").date()  # noqa: DTZ007


def parse_identity(text: StatementText) -> ChaseCreditCardIdentity:
    """Parse identity fields from a Chase credit-card statement."""
    full_text = text.text

    account_match = _ACCOUNT_PATTERN.search(full_text)

    if account_match is None:
        fallback_matches = tuple(
            _UNLABELED_ACCOUNT_PATTERN.finditer(full_text)
        )

        unique_accounts = {
            match.group("display"): match for match in fallback_matches
        }

        if len(unique_accounts) != 1:
            msg = "Chase credit-card account number was not found uniquely."
            raise ValueError(msg)

        account_match = next(iter(unique_accounts.values()))

    period_match = _PERIOD_PATTERN.search(full_text)
    if period_match is None:
        msg = "Chase credit-card statement period was not found."
        raise ValueError(msg)

    statement_date_match = _STATEMENT_DATE_PATTERN.search(full_text)
    if statement_date_match is None:
        msg = "Chase credit-card statement date was not found."
        raise ValueError(msg)

    statement_start = _parse_date(period_match.group("start"))
    statement_end = _parse_date(period_match.group("end"))
    statement_date = _parse_date(statement_date_match.group("date"))

    if statement_date != statement_end:
        msg = (
            "Chase credit-card statement date does not match the closing date."
        )
        raise ValueError(msg)

    return ChaseCreditCardIdentity(
        account=AccountIdentity(
            account_type=AccountType.CREDIT_CARD,
            display_number=account_match.group("display"),
            last4=account_match.group("last4"),
        ),
        statement_start=statement_start,
        statement_end=statement_end,
        statement_date=statement_date,
    )
