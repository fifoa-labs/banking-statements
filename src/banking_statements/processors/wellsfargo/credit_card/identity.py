"""
src/banking_statements/processors/wellsfargo/credit_card/identity.py

Identity parsing for supported Wells Fargo credit-card statements.
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
class WellsFargoCreditCardIdentity:
    """Identity fields parsed from a Wells Fargo credit-card statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ENDING_ACCOUNT_PATTERN = re.compile(
    r"Account ending in\s+(?P<last4>\d{4})",
)

_FULL_ACCOUNT_PATTERN = re.compile(
    r"Account Number\s+"
    r"(?P<display>"
    r"\d{4} \d{4} \d{4} (?P<last4>\d{4})"
    r")",
)

_PERIOD_PATTERN = re.compile(
    r"Statement Period\s+"
    r"(?P<start>\d{2}/\d{2}/\d{4})\s+to\s+"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
)

_END_ONLY_PERIOD_PATTERN = re.compile(
    r"Statement Period\s+to\s+"
    r"(?P<end>\d{2}/\d{2}/\d{4})",
)


def _parse_date(value: str) -> date:
    """Parse a Wells Fargo credit-card statement date."""
    return datetime.strptime(value, "%m/%d/%Y").date()  # noqa: DTZ007


def _parse_statement_period(
    full_text: str,
) -> tuple[date, date]:
    """Parse the supported Wells Fargo credit-card statement period."""
    period_match = _PERIOD_PATTERN.search(full_text)

    if period_match is not None:
        return (
            _parse_date(period_match.group("start")),
            _parse_date(period_match.group("end")),
        )

    end_only_match = _END_ONLY_PERIOD_PATTERN.search(full_text)

    if end_only_match is not None:
        statement_end = _parse_date(end_only_match.group("end"))

        return statement_end, statement_end

    msg = "Wells Fargo credit-card statement period was not found."
    raise ValueError(msg)


def parse_identity(text: StatementText) -> WellsFargoCreditCardIdentity:
    """Parse identity fields from a Wells Fargo credit-card statement."""
    full_text = text.text

    ending_match = _ENDING_ACCOUNT_PATTERN.search(full_text)
    if ending_match is None:
        msg = "Wells Fargo credit-card account ending was not found."
        raise ValueError(msg)

    last4 = ending_match.group("last4")

    full_account_match = _FULL_ACCOUNT_PATTERN.search(full_text)

    if full_account_match is not None:
        if full_account_match.group("last4") != last4:
            msg = "Wells Fargo credit-card account numbers do not agree."
            raise ValueError(msg)

        display_number = full_account_match.group("display")
    else:
        display_number = last4

    statement_start, statement_end = _parse_statement_period(full_text)

    return WellsFargoCreditCardIdentity(
        account=AccountIdentity(
            account_type=AccountType.CREDIT_CARD,
            display_number=display_number,
            last4=last4,
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
