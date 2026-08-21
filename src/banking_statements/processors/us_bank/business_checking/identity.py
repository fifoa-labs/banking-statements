"""
src/banking_statements/processors/us_bank/business_checking/identity.py

Identity parsing for supported U.S. Bank business-checking statements.
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
class USBankBusinessCheckingIdentity:
    """Identity fields parsed from a U.S. Bank business statement."""

    account: AccountIdentity
    statement_start: date
    statement_end: date


_ACCOUNT_PATTERN = re.compile(
    r"Account Number:?\s*"
    r"(?P<display>\d(?:[ -]?\d){11})\b",
    re.IGNORECASE,
)

_PERIOD_PATTERN = re.compile(
    r"Beginning Balance on\s+"
    r"(?P<start>[A-Z][a-z]{2}\s*\d{1,2})\s+"
    r"\$\s*[\d,]+\.\d{2}-?"
    r".*?"
    r"Ending Balance on\s+"
    r"(?P<end>[A-Z][a-z]{2}\s*\d{1,2},\s*\d{4})",
    re.DOTALL,
)


def _parse_end_date(value: str) -> date:
    """Parse a fully reported U.S. Bank business-checking date."""
    normalized = " ".join(value.split())
    return datetime.strptime(normalized, "%b %d, %Y").date()  # noqa: DTZ007


def _resolve_start_date(value: str, *, statement_end: date) -> date:
    """Resolve the abbreviated opening date against the reported end date."""
    normalized = " ".join(value.split())
    parsed = datetime.strptime(  # noqa: DTZ007
        f"{normalized} 2000",
        "%b %d %Y",
    )

    candidates: list[date] = []
    for year in (statement_end.year, statement_end.year - 1):
        try:
            candidate = date(year, parsed.month, parsed.day)
        except ValueError:
            continue

        if candidate <= statement_end:
            candidates.append(candidate)

    if not candidates:
        msg = f"Invalid U.S. Bank business-checking statement date: {value!r}."
        raise ValueError(msg)

    return max(candidates)


def parse_identity(text: StatementText) -> USBankBusinessCheckingIdentity:
    """Parse U.S. Bank business-checking account identity and period."""
    account_values = {
        re.sub(r"[ -]", "", match.group("display")): match.group("display")
        for match in _ACCOUNT_PATTERN.finditer(text.text)
    }

    if len(account_values) != 1:
        msg = (
            "U.S. Bank business-checking account number was not found "
            "uniquely."
        )
        raise ValueError(msg)

    period_matches = tuple(_PERIOD_PATTERN.finditer(text.text))
    period_values = {
        (match.group("start"), match.group("end")) for match in period_matches
    }

    if len(period_values) != 1:
        msg = (
            "U.S. Bank business-checking statement period was not found "
            "uniquely."
        )
        raise ValueError(msg)

    start_text, end_text = next(iter(period_values))
    statement_end = _parse_end_date(end_text)
    statement_start = _resolve_start_date(
        start_text,
        statement_end=statement_end,
    )

    normalized, display = next(iter(account_values.items()))

    return USBankBusinessCheckingIdentity(
        account=AccountIdentity(
            account_type=AccountType.CHECKING,
            display_number=display,
            last4=normalized[-4:],
        ),
        statement_start=statement_start,
        statement_end=statement_end,
    )
