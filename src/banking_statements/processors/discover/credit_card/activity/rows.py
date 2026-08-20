"""
src/banking_statements/processors/discover/credit_card/activity/rows.py

Logical activity-row reconstruction for Discover credit-card statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class DiscoverCreditCardActivitySection(StrEnum):
    """Economic activity families reported by Discover
    credit-card statements.
    """

    CREDIT = "credit"
    DEBIT = "debit"
    FEE = "fee"
    INTEREST = "interest"


@dataclass(frozen=True, slots=True)
class DiscoverCreditCardActivityRow:
    """One reconstructed Discover credit-card economic activity row."""

    transaction_date: str | None
    posting_date: str | None
    description: str
    amount: Decimal
    section: DiscoverCreditCardActivitySection
    raw_text: str


_LEGACY_ROW_PATTERN = re.compile(
    r"^(?:(?P<section_label>.+?)\s+)?"
    r"(?P<transaction_date>[A-Z][a-z]{2} \d{1,2})\s+"
    r"(?P<posting_date>[A-Z][a-z]{2} \d{1,2})\s+"
    r"(?P<description>.+?)\s+"
    r"\$?\s*(?P<amount>-?[\d,]+\.\d{2})$",
)

_CURRENT_ROW_PATTERN = re.compile(
    r"^(?P<transaction_date>\d{2}/\d{2})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>-?\$?[\d,]+\.\d{2})"
    r"(?:\s+(?P<adjacent_text>.+))?$",
)

_DATED_ROW_PREFIX_PATTERN = re.compile(
    r"^(?:"
    r"(?:.+?\s+)?[A-Z][a-z]{2} \d{1,2}\s+[A-Z][a-z]{2} \d{1,2}"
    r"|"
    r"\d{2}/\d{2}"
    r")\b",
)

_REFERENCE_LINE_PATTERN = re.compile(
    r"^[A-Z0-9]{8,}$",
)

_PERIOD_TOTAL_PATTERNS = {
    DiscoverCreditCardActivitySection.FEE: re.compile(
        r"TOTAL\s*FEES\s*FOR\s*THIS\s*PERIOD"
        r"\s*\$?\s*(?P<amount>[\d,]+\.\d{2})",
        re.IGNORECASE,
    ),
    DiscoverCreditCardActivitySection.INTEREST: re.compile(
        r"TOTAL\s*INTEREST\s*(?:CHARGED\s*)?"
        r"FOR\s*THIS\s*PERIOD"
        r"\s*\$?\s*(?P<amount>[\d,]+\.\d{2})",
        re.IGNORECASE,
    ),
}

_PERIOD_TOTAL_DESCRIPTIONS = {
    DiscoverCreditCardActivitySection.FEE: "FEES CHARGED",
    DiscoverCreditCardActivitySection.INTEREST: "INTEREST CHARGED",
}

_TRANSACTION_MARKERS = (
    "Transactions",
    "Transactions - continued",
)

_TRANSACTION_STOP_PREFIXES = (
    "FeesandInterestCharged",
    "Fees TOTALFEESFORTHISPERIOD",
)


def _parse_signed_amount(value: str) -> Decimal:
    """Parse a signed Discover transaction amount."""
    return Decimal(value.replace("$", "").replace(",", "").replace(" ", ""))


def _activity_section(amount: Decimal) -> DiscoverCreditCardActivitySection:
    """Infer Discover economic direction from the statement-reported sign."""
    if amount < Decimal("0"):
        return DiscoverCreditCardActivitySection.CREDIT

    return DiscoverCreditCardActivitySection.DEBIT


def _append_reference(
    row: DiscoverCreditCardActivityRow,
    line: str,
) -> DiscoverCreditCardActivityRow:
    """Preserve a merchant/reference continuation line in source evidence."""
    return replace(
        row,
        raw_text=f"{row.raw_text}\n{line}",
    )


def _build_legacy_row(
    match: re.Match[str],
    *,
    raw_text: str,
) -> DiscoverCreditCardActivityRow:
    """Build one row from the legacy transaction/post-date layout."""
    signed_amount = _parse_signed_amount(match.group("amount"))

    return DiscoverCreditCardActivityRow(
        transaction_date=match.group("transaction_date"),
        posting_date=match.group("posting_date"),
        description=match.group("description"),
        amount=abs(signed_amount),
        section=_activity_section(signed_amount),
        raw_text=raw_text,
    )


def _build_current_row(
    match: re.Match[str],
    *,
    raw_text: str,
) -> DiscoverCreditCardActivityRow:
    """Build one row from the current single-date transaction layout."""
    signed_amount = _parse_signed_amount(match.group("amount"))
    transaction_date = match.group("transaction_date")

    return DiscoverCreditCardActivityRow(
        transaction_date=transaction_date,
        posting_date=None,
        description=match.group("description"),
        amount=abs(signed_amount),
        section=_activity_section(signed_amount),
        raw_text=raw_text,
    )


def _parse_transaction_rows(
    text: str,
) -> list[DiscoverCreditCardActivityRow]:
    """Parse dated transaction rows from all supported Discover layouts."""
    rows: list[DiscoverCreditCardActivityRow] = []
    in_transactions = False
    last_row_index: int | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line in _TRANSACTION_MARKERS or line.startswith(
            "Transactions Cashback"
        ):
            in_transactions = True
            last_row_index = None
            continue

        if not in_transactions:
            continue

        if line.startswith(_TRANSACTION_STOP_PREFIXES):
            in_transactions = False
            last_row_index = None
            continue

        legacy_match = _LEGACY_ROW_PATTERN.fullmatch(line)

        if legacy_match is not None:
            rows.append(
                _build_legacy_row(
                    legacy_match,
                    raw_text=line,
                )
            )
            last_row_index = len(rows) - 1
            continue

        current_match = _CURRENT_ROW_PATTERN.fullmatch(line)

        if current_match is not None:
            rows.append(
                _build_current_row(
                    current_match,
                    raw_text=line,
                )
            )
            last_row_index = len(rows) - 1
            continue

        if _DATED_ROW_PREFIX_PATTERN.match(line):
            msg = f"Unrecognized Discover credit-card transaction row: {line}"
            raise ValueError(msg)

        if (
            last_row_index is not None
            and _REFERENCE_LINE_PATTERN.fullmatch(line) is not None
        ):
            rows[last_row_index] = _append_reference(
                rows[last_row_index],
                line,
            )

    return rows


def _parse_period_total(
    text: str,
    *,
    section: DiscoverCreditCardActivitySection,
) -> DiscoverCreditCardActivityRow | None:
    """Parse one nonzero statement-period fee or interest total."""
    pattern = _PERIOD_TOTAL_PATTERNS[section]
    match = pattern.search(text)

    if match is None:
        msg = (
            "Discover credit-card activity total "
            f"{section.value!r} was not found."
        )
        raise ValueError(msg)

    amount = Decimal(match.group("amount").replace(",", ""))

    if amount == Decimal("0"):
        return None

    return DiscoverCreditCardActivityRow(
        transaction_date=None,
        posting_date=None,
        description=_PERIOD_TOTAL_DESCRIPTIONS[section],
        amount=amount,
        section=section,
        raw_text=match.group(0),
    )


def parse_activity_rows(
    text: StatementText,
) -> tuple[DiscoverCreditCardActivityRow, ...]:
    """Parse Discover credit-card economic activity across proven layouts."""
    rows = _parse_transaction_rows(text.text)

    for section in (
        DiscoverCreditCardActivitySection.FEE,
        DiscoverCreditCardActivitySection.INTEREST,
    ):
        period_total = _parse_period_total(
            text.text,
            section=section,
        )

        if period_total is not None:
            rows.append(period_total)

    return tuple(rows)
