"""
src/banking_statements/processors/american_express/personal_loan/identity.py

Identity parsing for American Express personal-loan statements.
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
class AmericanExpressPersonalLoanIdentity:
    """Identity fields parsed from an American Express
    personal-loan invoice.
    """

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Loan Account Ending\s*(?P<display>\d-\d{5})",
)

_INVOICE_DATE_PATTERN = re.compile(
    r"(?<!Next )Invoice Date\s*(?P<date>\d{2}/\d{2}/\d{2})",
)

_NEXT_INVOICE_DATE_PATTERN = re.compile(
    r"Next Invoice Date\s*(?P<date>\d{2}/\d{2}/\d{2})",
)

_ACTIVITY_DATE_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2}/\d{2})\*?\s+",
    re.MULTILINE,
)


def _parse_date(value: str) -> date:
    """Parse an American Express personal-loan invoice date."""
    return datetime.strptime(value, "%m/%d/%y").date()  # noqa: DTZ007


def parse_identity(
    text: StatementText,
) -> AmericanExpressPersonalLoanIdentity:
    """Parse identity fields from an American Express personal-loan invoice."""
    account_match = _ACCOUNT_PATTERN.search(text.text)
    if account_match is None:
        msg = "American Express personal-loan account ending was not found."
        raise ValueError(msg)

    invoice_match = _INVOICE_DATE_PATTERN.search(text.text)
    if invoice_match is None:
        msg = "American Express personal-loan invoice date was not found."
        raise ValueError(msg)

    next_invoice_match = _NEXT_INVOICE_DATE_PATTERN.search(text.text)
    if next_invoice_match is None:
        msg = "American Express personal-loan next invoice date was not found."
        raise ValueError(msg)

    statement_end = _parse_date(invoice_match.group("date"))
    next_invoice_date = _parse_date(next_invoice_match.group("date"))

    if next_invoice_date <= statement_end:
        msg = (
            "American Express personal-loan next invoice date must be "
            "after the invoice date."
        )
        raise ValueError(msg)

    activity_dates = tuple(
        _parse_date(match.group("date"))
        for match in _ACTIVITY_DATE_PATTERN.finditer(text.text)
    )
    statement_start = min(activity_dates, default=statement_end)

    if statement_start > statement_end:
        msg = (
            "American Express personal-loan activity starts after "
            "the invoice date."
        )
        raise ValueError(msg)

    display_number = account_match.group("display")
    account_digits = re.sub(r"\D", "", display_number)

    return AmericanExpressPersonalLoanIdentity(
        account=AccountIdentity(
            account_type=AccountType.LOAN,
            display_number=display_number,
            last4=account_digits[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
