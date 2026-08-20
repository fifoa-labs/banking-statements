"""
src/banking_statements/processors/american_express/business_line_of_credit/identity.py

Identity parsing for American Express business line-of-credit statements.
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
class AmericanExpressBusinessLineOfCreditIdentity:
    """Identity fields parsed from an American Express
    line-of-credit statement.
    """

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Account number\s+(?P<display>\d{6})\b",
)

_STATEMENT_DATE_PATTERN = re.compile(
    r"Statement Date\s+(?P<date>\d{2}/\d{2}/\d{4})",
)

_PERIOD_PATTERN = re.compile(
    r"For the Period\s+"
    r"(?P<start>\d{2}/\d{2}/\d{4})\s*-\s*"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
)


def _parse_date(value: str) -> date:
    """Parse an American Express business line-of-credit statement date."""
    return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007


def parse_identity(
    text: StatementText,
) -> AmericanExpressBusinessLineOfCreditIdentity:
    """Parse identity fields from an American Express
    line-of-credit statement."""

    full_text = text.text

    account_match = _ACCOUNT_PATTERN.search(full_text)
    if account_match is None:
        msg = (
            "American Express business line-of-credit account number "
            "was not found."
        )
        raise ValueError(msg)

    statement_date_match = _STATEMENT_DATE_PATTERN.search(full_text)
    if statement_date_match is None:
        msg = (
            "American Express business line-of-credit statement date "
            "was not found."
        )
        raise ValueError(msg)

    period_match = _PERIOD_PATTERN.search(full_text)
    if period_match is None:
        msg = (
            "American Express business line-of-credit statement period "
            "was not found."
        )
        raise ValueError(msg)

    statement_date = _parse_date(statement_date_match.group("date"))
    statement_start = _parse_date(period_match.group("start"))
    statement_end = _parse_date(period_match.group("end"))

    if statement_date != statement_end:
        msg = (
            "American Express business line-of-credit statement date does "
            "not match the statement period end."
        )
        raise ValueError(msg)

    display_number = account_match.group("display")

    return AmericanExpressBusinessLineOfCreditIdentity(
        account=AccountIdentity(
            account_type=AccountType.LINE_OF_CREDIT,
            display_number=display_number,
            last4=display_number[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
