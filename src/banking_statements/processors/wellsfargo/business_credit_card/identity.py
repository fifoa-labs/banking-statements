"""
src/banking_statements/processors/wellsfargo/business_credit_card/identity.py

Identity parsing for supported Wells Fargo business credit-card statements.
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
class WellsFargoBusinessCreditCardIdentity:
    """Identity fields parsed from a Wells Fargo
    business credit-card statement.
    """

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Account Number\s+"
    r"(?P<display>"
    r"\d{4} \d{4} \d{4} (?P<last4>\d{4})"
    r")",
)

_ENDING_ACCOUNT_PATTERN = re.compile(
    r"account ending\s*(?P<last4>\d{4})",
    re.IGNORECASE,
)

_CLOSING_DATE_PATTERN = re.compile(
    r"Statement Closing Date\s+"
    r"(?P<date>\d{2}/\d{2}/\d{2})",
)

_BILLING_DAYS_PATTERN = re.compile(
    r"Days in Billing Cycle\s+"
    r"(?P<days>\d+)",
)


def _parse_date(value: str) -> date:
    """Parse a Wells Fargo business credit-card closing date."""
    return datetime.strptime(value, "%m/%d/%y").date()  # noqa: DTZ007


def parse_identity(
    text: StatementText,
) -> WellsFargoBusinessCreditCardIdentity:
    """Parse identity fields from a Wells Fargo
    business credit-card statement.
    """
    full_text = text.text

    account_match = _ACCOUNT_PATTERN.search(full_text)
    if account_match is None:
        msg = "Wells Fargo business credit-card account number was not found."
        raise ValueError(msg)

    display_number = account_match.group("display")
    last4 = account_match.group("last4")

    ending_matches = {
        match.group("last4")
        for match in _ENDING_ACCOUNT_PATTERN.finditer(full_text)
    }

    if ending_matches and ending_matches != {last4}:
        msg = "Wells Fargo business credit-card account numbers do not agree."
        raise ValueError(msg)

    closing_match = _CLOSING_DATE_PATTERN.search(full_text)
    if closing_match is None:
        msg = "Wells Fargo business credit-card closing date was not found."
        raise ValueError(msg)

    billing_days_match = _BILLING_DAYS_PATTERN.search(full_text)
    if billing_days_match is None:
        msg = "Wells Fargo business credit-card billing cycle was not found."
        raise ValueError(msg)

    billing_days = int(billing_days_match.group("days"))

    statement_end = _parse_date(closing_match.group("date"))

    statement_start = (
        statement_end
        if billing_days == 0
        else statement_end - timedelta(days=billing_days - 1)
    )

    return WellsFargoBusinessCreditCardIdentity(
        account=AccountIdentity(
            account_type=AccountType.CREDIT_CARD,
            display_number=display_number,
            last4=last4,
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
