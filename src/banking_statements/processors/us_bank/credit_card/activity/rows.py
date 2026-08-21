"""
src/banking_statements/processors/us_bank/credit_card/activity/rows.py

Logical activity-row reconstruction for U.S. Bank credit-card statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class USBankCreditCardActivitySection(StrEnum):
    """Economic activity families reported by U.S. Bank credit cards."""

    CREDIT = "credit"
    DEBIT = "debit"
    FEE = "fee"
    INTEREST = "interest"


@dataclass(frozen=True, slots=True)
class USBankCreditCardActivityRow:
    """One reconstructed U.S. Bank credit-card activity row."""

    posting_date: str
    transaction_date: str | None
    description: str
    amount: Decimal
    direction_is_credit: bool
    section: USBankCreditCardActivitySection
    page: int
    raw_text: str


_SECTION_MARKERS = {
    "Payments and Other Credits": USBankCreditCardActivitySection.CREDIT,
    "Purchases and Other Debits": USBankCreditCardActivitySection.DEBIT,
    "Fees": USBankCreditCardActivitySection.FEE,
    "Interest Charged": USBankCreditCardActivitySection.INTEREST,
}

_TWO_DATE_ROW_PATTERN = re.compile(
    r"^(?P<post>\d{2}/\d{2})\s+"
    r"(?P<transaction>\d{2}/\d{2})\s+"
    r"(?:(?P<reference>\d{4})\s+)?"
    r"(?P<description>.+?)\s+"
    r"\$(?P<amount>[\d,]+\.\d{2})(?P<credit>CR)?$",
)

_ONE_DATE_ROW_PATTERN = re.compile(
    r"^(?P<post>\d{2}/\d{2})\s+"
    r"(?:(?P<reference>\d{4})\s+)?"
    r"(?P<description>.+?)\s+"
    r"\$(?P<amount>[\d,]+\.\d{2})(?P<credit>CR)?$",
)

_DATED_PREFIX_PATTERN = re.compile(r"^\d{2}/\d{2}\b")

_TOTAL_PATTERN = re.compile(
    r"^(?P<label>TOTAL THIS PERIOD|TOTAL FEES THIS PERIOD|"
    r"TOTAL INTEREST THIS PERIOD)\s+"
    r"\$(?P<amount>[\d,]+\.\d{2})(?P<credit>CR)?$",
)

_HEADER_LINES = frozenset(
    {
        "Post Trans",
        "Date Date Ref # Transaction Description Amount",
        "Post",
        "Date Transaction Description Amount",
    }
)

_CONTINUATION_PATTERNS = (
    re.compile(r"^MERCHANDISE/SERVICE RETURN$"),
    re.compile(r"^DEBIT ADJUSTMENT$"),
    re.compile(r"^CREDIT ADJUSTMENT$"),
    re.compile(r"^FOLIO:\s+.+$"),
)

_STOP_PREFIXES = (
    "Interest Charge Calculation",
    "Contact Us",
)


def _parse_amount(value: str) -> Decimal:
    """Parse one unsigned U.S. Bank credit-card activity amount."""
    return Decimal(value.replace(",", ""))


def _append_evidence(
    row: USBankCreditCardActivityRow,
    line: str,
) -> USBankCreditCardActivityRow:
    """Append a supported continuation line to transaction evidence."""
    return replace(row, raw_text=f"{row.raw_text}\n{line}")


def _row_from_match(
    match: re.Match[str],
    *,
    section: USBankCreditCardActivitySection,
    page: int,
    raw_text: str,
) -> USBankCreditCardActivityRow:
    """Build one normalized raw activity row from a regex match."""
    return USBankCreditCardActivityRow(
        posting_date=match.group("post"),
        transaction_date=match.groupdict().get("transaction"),
        description=match.group("description"),
        amount=_parse_amount(match.group("amount")),
        direction_is_credit=(
            match.group("credit") is not None
            or section is USBankCreditCardActivitySection.CREDIT
        ),
        section=section,
        page=page,
        raw_text=raw_text,
    )


def _expected_total_label(section: USBankCreditCardActivitySection) -> str:
    """Return the period-total label belonging to an activity section."""
    if section is USBankCreditCardActivitySection.FEE:
        return "TOTAL FEES THIS PERIOD"
    if section is USBankCreditCardActivitySection.INTEREST:
        return "TOTAL INTEREST THIS PERIOD"
    return "TOTAL THIS PERIOD"


def _validate_section_total(
    rows: list[USBankCreditCardActivityRow],
    *,
    section: USBankCreditCardActivitySection,
    reported_amount: Decimal,
    reported_credit: bool,
) -> None:
    """Require parsed section economics to equal its reported period total."""
    net = sum(
        (
            -row.amount if row.direction_is_credit else row.amount
            for row in rows
            if row.section is section
        ),
        start=Decimal("0"),
    )
    reported = -reported_amount if reported_credit else reported_amount

    if net != reported:
        msg = (
            "U.S. Bank credit-card parsed activity does not match the "
            f"reported {section.value} period total."
        )
        raise ValueError(msg)


def parse_activity_rows(  # noqa: C901, PLR0912
    text: StatementText,
) -> tuple[USBankCreditCardActivityRow, ...]:
    """Parse sectioned U.S. Bank credit-card economic activity."""
    rows: list[USBankCreditCardActivityRow] = []
    section: USBankCreditCardActivitySection | None = None
    last_row_index: int | None = None

    for page in text.pages:
        for raw_line in page.text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if line == "Transactions":
                section = None
                last_row_index = None
                continue

            discovered_section = _SECTION_MARKERS.get(line)
            if discovered_section is not None:
                section = discovered_section
                last_row_index = None
                continue

            if section is None:
                continue

            if line in _HEADER_LINES:
                continue

            total_match = _TOTAL_PATTERN.fullmatch(line)
            if total_match is not None:
                expected = _expected_total_label(section)
                if total_match.group("label") != expected:
                    msg = (
                        "U.S. Bank credit-card activity total does not match "
                        f"the active section: {line}"
                    )
                    raise ValueError(msg)

                _validate_section_total(
                    rows,
                    section=section,
                    reported_amount=_parse_amount(total_match.group("amount")),
                    reported_credit=total_match.group("credit") is not None,
                )
                section = None
                last_row_index = None
                continue

            if line.startswith(_STOP_PREFIXES):
                section = None
                last_row_index = None
                continue

            row_match = _TWO_DATE_ROW_PATTERN.fullmatch(line)
            if row_match is None:
                row_match = _ONE_DATE_ROW_PATTERN.fullmatch(line)

            if row_match is not None:
                rows.append(
                    _row_from_match(
                        row_match,
                        section=section,
                        page=page.number,
                        raw_text=line,
                    )
                )
                last_row_index = len(rows) - 1
                continue

            if _DATED_PREFIX_PATTERN.match(line):
                msg = (
                    "Unrecognized U.S. Bank credit-card transaction row: "
                    f"{line}"
                )
                raise ValueError(msg)

            if last_row_index is not None and any(
                pattern.fullmatch(line) is not None
                for pattern in _CONTINUATION_PATTERNS
            ):
                rows[last_row_index] = _append_evidence(
                    rows[last_row_index],
                    line,
                )

    return tuple(rows)
