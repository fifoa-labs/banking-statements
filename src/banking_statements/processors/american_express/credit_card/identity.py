"""
src/banking_statements/processors/american_express/credit_card/identity.py

Identity parsing for supported American Express credit-card statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from banking_statements.domain import AccountIdentity, AccountType

if TYPE_CHECKING:
    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class AmericanExpressCreditCardIdentity:
    """Identity fields parsed from an American Express
    credit-card statement.
    """

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Account Ending\s*(?P<display>\d-\d{5})",
)

_CLOSING_DATE_PATTERN = re.compile(
    r"Closing Date\s*(?P<date>\d{2}/\d{2}/\d{2})",
)

_BILLING_DAYS_PATTERN = re.compile(
    r"Days in Billing Period:\s*(?P<days>\d+)",
)


def _parse_date(value: str) -> date:
    """Parse an American Express statement date."""
    return datetime.strptime(value, "%m/%d/%y").date()  # noqa: DTZ007


def parse_identity(
    text: StatementText,
) -> AmericanExpressCreditCardIdentity:
    """Parse identity fields from an American Express credit-card statement."""
    full_text = text.text

    account_match = _ACCOUNT_PATTERN.search(full_text)
    if account_match is None:
        msg = "American Express credit-card account ending was not found."
        raise ValueError(msg)

    closing_match = _CLOSING_DATE_PATTERN.search(full_text)
    if closing_match is None:
        msg = "American Express credit-card closing date was not found."
        raise ValueError(msg)

    billing_days_match = _BILLING_DAYS_PATTERN.search(full_text)
    if billing_days_match is None:
        msg = "American Express credit-card billing period was not found."
        raise ValueError(msg)

    billing_days = int(billing_days_match.group("days"))
    if billing_days < 1:
        msg = "American Express credit-card billing period must be positive."
        raise ValueError(msg)

    display_number = account_match.group("display")
    account_digits = re.sub(r"\D", "", display_number)
    statement_end = _parse_date(closing_match.group("date"))
    statement_start = statement_end - timedelta(days=billing_days - 1)

    return AmericanExpressCreditCardIdentity(
        account=AccountIdentity(
            account_type=AccountType.CREDIT_CARD,
            display_number=display_number,
            last4=account_digits[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
