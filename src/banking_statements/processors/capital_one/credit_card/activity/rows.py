"""
src/banking_statements/processors/capital_one/credit_card/activity/rows.py

Logical activity-row reconstruction for Capital One credit-card statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class CapitalOneCreditCardActivitySection(StrEnum):
    """Economic activity families reported by Capital One statements."""

    CREDIT = "credit"
    DEBIT = "debit"
    FEE = "fee"
    INTEREST = "interest"


@dataclass(frozen=True, slots=True)
class CapitalOneCreditCardActivityRow:
    """One reconstructed Capital One credit-card economic activity row."""

    transaction_date: str | None
    posting_date: str | None
    description: str
    amount: Decimal
    section: CapitalOneCreditCardActivitySection
    card_last4: str | None
    raw_text: str


_CARD_SECTION_PATTERN = re.compile(
    r"^.+?\s+#(?P<last4>\d{4}):\s+"
    r"(?P<section>Payments, Credits and Adjustments|Transactions)$",
)

_ROW_PATTERN = re.compile(
    r"^(?P<transaction_date>[A-Z][a-z]{2} \d{1,2})\s+"
    r"(?P<posting_date>[A-Z][a-z]{2} \d{1,2})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>-?\s*\$[\d,]+\.\d{2})$",
)

_DATED_ROW_PREFIX_PATTERN = re.compile(
    r"^[A-Z][a-z]{2} \d{1,2}\s+[A-Z][a-z]{2} \d{1,2}\b",
)

_FOREIGN_CURRENCY_CONTINUATION_PATTERNS = (
    re.compile(r"^\$[\d,]+\.\d{2}$"),
    re.compile(r"^[A-Z]{3}$"),
    re.compile(r"^\d+\.\d+\s+Exchange Rate$"),
)

_FEE_TOTAL_PATTERN = re.compile(
    r"^Total Fees for This Period\s+"
    r"(?P<amount>\$[\d,]+\.\d{2})$",
    re.MULTILINE,
)

_INTEREST_TOTAL_PATTERN = re.compile(
    r"^Total Interest for This Period\s+"
    r"(?P<amount>\$[\d,]+\.\d{2})$",
    re.MULTILINE,
)


def _parse_amount(value: str) -> Decimal:
    """Parse one Capital One activity amount."""
    return Decimal(value.replace("$", "").replace(",", "").replace(" ", ""))


def _section_from_label(
    label: str,
) -> CapitalOneCreditCardActivitySection:
    """Map one Capital One cardholder activity label to economics."""
    if label == "Payments, Credits and Adjustments":
        return CapitalOneCreditCardActivitySection.CREDIT

    return CapitalOneCreditCardActivitySection.DEBIT


def _append_raw_text(
    row: CapitalOneCreditCardActivityRow,
    line: str,
) -> CapitalOneCreditCardActivityRow:
    """Preserve one foreign-currency continuation in source evidence."""
    return replace(
        row,
        raw_text=f"{row.raw_text}\n{line}",
    )


def _parse_period_total(
    text: str,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> tuple[Decimal, str]:
    """Parse one required Capital One statement-period activity total."""
    matches = tuple(pattern.finditer(text))
    amounts = {_parse_amount(match.group("amount")) for match in matches}

    if len(amounts) != 1 or not matches:
        msg = (
            "Capital One credit-card activity total "
            f"{field!r} was not found uniquely."
        )
        raise ValueError(msg)

    amount = next(iter(amounts))
    raw_text = next(
        match.group(0)
        for match in matches
        if _parse_amount(match.group("amount")) == amount
    )

    return amount, raw_text


def parse_activity_rows(  # noqa: C901
    text: StatementText,
) -> tuple[CapitalOneCreditCardActivityRow, ...]:
    """Parse Capital One credit-card activity across the proven layout."""
    rows: list[CapitalOneCreditCardActivityRow] = []
    section: CapitalOneCreditCardActivitySection | None = None
    card_last4: str | None = None
    last_row_index: int | None = None

    for raw_line in text.text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        card_section_match = _CARD_SECTION_PATTERN.fullmatch(line)
        if card_section_match is not None:
            section = _section_from_label(
                card_section_match.group("section"),
            )
            card_last4 = card_section_match.group("last4")
            last_row_index = None
            continue

        if line == "Fees":
            section = CapitalOneCreditCardActivitySection.FEE
            card_last4 = None
            last_row_index = None
            continue

        if line == "Interest Charged":
            section = None
            card_last4 = None
            last_row_index = None
            continue

        if section is None:
            continue

        row_match = _ROW_PATTERN.fullmatch(line)
        if row_match is not None:
            signed_amount = _parse_amount(row_match.group("amount"))
            rows.append(
                CapitalOneCreditCardActivityRow(
                    transaction_date=row_match.group("transaction_date"),
                    posting_date=row_match.group("posting_date"),
                    description=row_match.group("description"),
                    amount=abs(signed_amount),
                    section=section,
                    card_last4=card_last4,
                    raw_text=line,
                )
            )
            last_row_index = len(rows) - 1
            continue

        if _DATED_ROW_PREFIX_PATTERN.match(line):
            msg = (
                f"Unrecognized Capital One credit-card transaction row: {line}"
            )
            raise ValueError(msg)

        if last_row_index is not None and any(
            pattern.fullmatch(line) is not None
            for pattern in _FOREIGN_CURRENCY_CONTINUATION_PATTERNS
        ):
            rows[last_row_index] = _append_raw_text(
                rows[last_row_index],
                line,
            )

    fee_total, _ = _parse_period_total(
        text.text,
        field="fee",
        pattern=_FEE_TOTAL_PATTERN,
    )
    parsed_fee_total = sum(
        (
            row.amount
            for row in rows
            if row.section is CapitalOneCreditCardActivitySection.FEE
        ),
        start=Decimal("0"),
    )

    if parsed_fee_total != fee_total:
        msg = (
            "Capital One credit-card parsed fee rows do not match the "
            "reported period fee total."
        )
        raise ValueError(msg)

    interest_total, interest_raw_text = _parse_period_total(
        text.text,
        field="interest",
        pattern=_INTEREST_TOTAL_PATTERN,
    )

    if interest_total != Decimal("0"):
        rows.append(
            CapitalOneCreditCardActivityRow(
                transaction_date=None,
                posting_date=None,
                description="INTEREST CHARGED",
                amount=interest_total,
                section=CapitalOneCreditCardActivitySection.INTEREST,
                card_last4=None,
                raw_text=interest_raw_text,
            )
        )

    return tuple(rows)
