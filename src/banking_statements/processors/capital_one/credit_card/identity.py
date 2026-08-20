"""
src/banking_statements/processors/capital_one/credit_card/identity.py

Identity parsing for supported Capital One credit-card statements.
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
class CapitalOneCreditCardIdentity:
    """Identity fields parsed from a Capital One credit-card statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date
    billing_days: int


_ACCOUNT_ENDING_PATTERNS = (
    re.compile(
        r"Venture X Card \| Visa Infinite ending in\s*(?P<last4>\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"Account ending in\s*(?P<last4>\d{4})\b",
        re.IGNORECASE,
    ),
)

_PERIOD_PATTERN = re.compile(
    r"(?P<start>[A-Z][a-z]{2} \d{1,2}, \d{4})"
    r"\s*-\s*"
    r"(?P<end>[A-Z][a-z]{2} \d{1,2}, \d{4})"
    r"\s*\|\s*"
    r"(?P<days>\d+)\s+days in Billing Cycle",
    re.IGNORECASE,
)


def _parse_date(value: str) -> date:
    """Parse one Capital One statement-period date."""
    return datetime.strptime(value, "%b %d, %Y").date()  # noqa: DTZ007


def parse_identity(text: StatementText) -> CapitalOneCreditCardIdentity:
    """Parse Capital One credit-card account identity and statement period."""
    account_endings = {
        match.group("last4")
        for pattern in _ACCOUNT_ENDING_PATTERNS
        for match in pattern.finditer(text.text)
    }

    if len(account_endings) != 1:
        msg = "Capital One credit-card account ending was not found uniquely."
        raise ValueError(msg)

    period_values = {
        (
            match.group("start"),
            match.group("end"),
            int(match.group("days")),
        )
        for match in _PERIOD_PATTERN.finditer(text.text)
    }

    if len(period_values) != 1:
        msg = (
            "Capital One credit-card statement period was not found uniquely."
        )
        raise ValueError(msg)

    start_text, end_text, billing_days = next(iter(period_values))
    statement_start = _parse_date(start_text)
    statement_end = _parse_date(end_text)

    if statement_start > statement_end:
        msg = "Capital One credit-card statement period starts after it ends."
        raise ValueError(msg)

    actual_billing_days = (statement_end - statement_start).days + 1
    if actual_billing_days != billing_days:
        msg = (
            "Capital One credit-card billing-cycle day count does not match "
            "the statement period."
        )
        raise ValueError(msg)

    last4 = next(iter(account_endings))

    return CapitalOneCreditCardIdentity(
        account=AccountIdentity(
            account_type=AccountType.CREDIT_CARD,
            display_number=last4,
            last4=last4,
        ),
        statement_start=statement_start,
        statement_end=statement_end,
        billing_days=billing_days,
    )
