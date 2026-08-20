"""
src/banking_statements/processors/capital_one/business_credit_card/activity/rows.py

Logical activity-row reconstruction for Capital One business credit cards.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class CapitalOneBusinessCreditCardActivitySection(StrEnum):
    """Economic activity families reported by Capital One business cards."""

    CREDIT = "credit"
    DEBIT = "debit"
    FEE = "fee"
    INTEREST = "interest"


@dataclass(frozen=True, slots=True)
class CapitalOneBusinessCreditCardActivityRow:
    """One reconstructed Capital One business-card economic activity row."""

    transaction_date: str | None
    posting_date: str | None
    description: str
    amount: Decimal
    section: CapitalOneBusinessCreditCardActivitySection
    card_last4: str | None
    raw_text: str


_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
_AMOUNT_TEXT = r"-?\s*\$[\d,]+\.\d{2}"

_CURRENT_ROW_PATTERN = re.compile(
    rf"^(?P<transaction_date>{_MONTH} \d{{1,2}})\s+"
    rf"(?P<posting_date>{_MONTH} \d{{1,2}})\s+"
    rf"(?P<description>.+?)\s+"
    rf"(?P<amount>{_AMOUNT_TEXT})$",
)

_CURRENT_DATED_PREFIX_PATTERN = re.compile(
    rf"^{_MONTH} \d{{1,2}}\s+{_MONTH} \d{{1,2}}\b",
)

_LEGACY_DATE_PATTERN = re.compile(
    rf"{_MONTH} \d{{1,2}}\b",
)

_AMOUNT_PATTERN = re.compile(_AMOUNT_TEXT)

_CARD_SECTION_PATTERN = re.compile(
    r"^.+?\s+#(?P<last4>\d{4}):\s+"
    r"(?P<section>Payments, Credits and Adjustments|Credits|Transactions)$",
)

_TRANSACTION_TOTAL_PATTERN = re.compile(
    r"Total Transactions for This Period\s+"
    r"(?P<amount>\$[\d,]+\.\d{2})",
)

_FEE_TOTAL_PATTERN = re.compile(
    r"Total Fees for This Period\s+"
    r"(?P<amount>\$[\d,]+\.\d{2})",
)

_INTEREST_TOTAL_PATTERN = re.compile(
    r"Total Interest for This Period\s+"
    r"(?P<amount>\$[\d,]+\.\d{2})",
)

_CURRENT_CONTINUATION_PATTERNS = (
    re.compile(r"^\$[\d,]+\.\d{2}$"),
    re.compile(r"^[A-Z]{3}$"),
    re.compile(r"^\d+\.\d+\s+Exchange Rate$"),
    re.compile(r"^TK#:\s+.+$"),
    re.compile(r"^ORIG:\s+.+$"),
    re.compile(r"^(?:ARRIVE|RETURN):\s+.+$"),
)

_LEGACY_TITLE_MARKER = "Spark® Visa Signature Business Account Ending in"
_SPARK_CURRENT_TITLE_MARKER = (
    "Spark Cash credit card | Visa Signature Business ending in"
)
_VENTURE_X_BUSINESS_TITLE_MARKER = (
    "Venture X Business card | Visa Infinite Business ending in"
)


def _parse_amount(value: str) -> Decimal:
    """Parse one Capital One business-card activity amount."""
    return Decimal(value.replace("$", "").replace(",", "").replace(" ", ""))


def _economic_section(
    amount: Decimal,
) -> CapitalOneBusinessCreditCardActivitySection:
    """Return transaction economics from the statement-reported sign."""
    if amount < Decimal("0"):
        return CapitalOneBusinessCreditCardActivitySection.CREDIT

    return CapitalOneBusinessCreditCardActivitySection.DEBIT


def _append_raw_text(
    row: CapitalOneBusinessCreditCardActivityRow,
    line: str,
) -> CapitalOneBusinessCreditCardActivityRow:
    """Preserve one continuation line in source evidence."""
    return replace(
        row,
        raw_text=f"{row.raw_text}\n{line}",
    )


def _unique_reported_total(
    text: str,
    *,
    field: str,
    pattern: re.Pattern[str],
    required: bool,
) -> Decimal | None:
    """Parse one uniquely reported Capital One activity total."""
    matches = tuple(pattern.finditer(text))

    if not matches:
        if required:
            msg = (
                "Capital One business credit-card activity total "
                f"{field!r} was not found."
            )
            raise ValueError(msg)

        return None

    amounts = {_parse_amount(match.group("amount")) for match in matches}

    if len(amounts) != 1:
        msg = (
            "Capital One business credit-card activity total "
            f"{field!r} was not found uniquely."
        )
        raise ValueError(msg)

    return next(iter(amounts))


def _first_activity_index(lines: list[str]) -> int:
    """Return the first proven business-card transaction section index."""
    for index, line in enumerate(lines):
        if line == "Transactions":
            return index

        if line.startswith(
            (
                "Transactions Transactions",
                "Transactions Interest Charge Calculation",
            )
        ):
            return index

    msg = "Capital One business credit-card transaction section was not found."
    raise ValueError(msg)


def _legacy_segments(line: str) -> tuple[str, ...]:
    """Split one legacy flattened line into date-led transaction segments."""
    starts = tuple(_LEGACY_DATE_PATTERN.finditer(line))
    segments: list[str] = []

    for index, match in enumerate(starts):
        end = (
            starts[index + 1].start() if index + 1 < len(starts) else len(line)
        )
        segments.append(line[match.start() : end].strip())

    return tuple(segments)


def _parse_legacy_transaction_rows(
    text: str,
) -> list[CapitalOneBusinessCreditCardActivityRow]:
    """Parse the legacy single-date Spark layout including merged columns."""
    lines = text.splitlines()
    start = _first_activity_index(lines)
    rows: list[CapitalOneBusinessCreditCardActivityRow] = []

    for line in lines[start:]:
        for segment in _legacy_segments(line):
            date_match = cast(
                "re.Match[str]",
                _LEGACY_DATE_PATTERN.match(segment),
            )
            amount_match = _AMOUNT_PATTERN.search(segment)

            if amount_match is None:
                msg = (
                    "Unrecognized Capital One business credit-card legacy "
                    f"transaction row: {segment}"
                )
                raise ValueError(msg)

            amount = _parse_amount(amount_match.group(0))
            description = segment[
                date_match.end() : amount_match.start()
            ].strip()

            rows.append(
                CapitalOneBusinessCreditCardActivityRow(
                    transaction_date=date_match.group(0),
                    posting_date=None,
                    description=description,
                    amount=abs(amount),
                    section=_economic_section(amount),
                    card_last4=None,
                    raw_text=segment,
                )
            )

    return rows


def _parse_current_transaction_rows(
    text: str,
) -> list[CapitalOneBusinessCreditCardActivityRow]:
    """Parse current Spark and Venture X Business transaction layouts."""
    lines = text.splitlines()
    start = _first_activity_index(lines)
    rows: list[CapitalOneBusinessCreditCardActivityRow] = []
    card_last4: str | None = None
    last_row_index: int | None = None

    for raw_line in lines[start:]:
        line = raw_line.strip()

        if line == "Fees":
            break

        if not line:
            continue

        card_match = _CARD_SECTION_PATTERN.fullmatch(line)
        if card_match is not None:
            card_last4 = card_match.group("last4")
            last_row_index = None
            continue

        row_match = _CURRENT_ROW_PATTERN.fullmatch(line)

        if row_match is not None:
            amount = _parse_amount(row_match.group("amount"))
            rows.append(
                CapitalOneBusinessCreditCardActivityRow(
                    transaction_date=row_match.group("transaction_date"),
                    posting_date=row_match.group("posting_date"),
                    description=row_match.group("description"),
                    amount=abs(amount),
                    section=_economic_section(amount),
                    card_last4=card_last4,
                    raw_text=line,
                )
            )
            last_row_index = len(rows) - 1
            continue

        if _CURRENT_DATED_PREFIX_PATTERN.match(line):
            msg = (
                "Unrecognized Capital One business credit-card transaction "
                f"row: {line}"
            )
            raise ValueError(msg)

        if last_row_index is not None and any(
            pattern.fullmatch(line) is not None
            for pattern in _CURRENT_CONTINUATION_PATTERNS
        ):
            rows[last_row_index] = _append_raw_text(
                rows[last_row_index],
                line,
            )

    return rows


def _parse_fee_rows(
    text: str,
) -> list[CapitalOneBusinessCreditCardActivityRow]:
    """Parse dated Capital One business-card fees."""
    if _LEGACY_TITLE_MARKER in text:
        legacy_total = _unique_reported_total(
            text,
            field="fee",
            pattern=_FEE_TOTAL_PATTERN,
            required=True,
        )

        if legacy_total == Decimal("0"):
            return []

        msg = (
            "Capital One business credit-card legacy nonzero fee rows are "
            "not supported by the proven grammar."
        )
        raise ValueError(msg)

    lines = text.splitlines()
    fee_index = next(
        (index for index, line in enumerate(lines) if line == "Fees"),
        None,
    )

    if fee_index is None:
        msg = "Capital One business credit-card fee section was not found."
        raise ValueError(msg)

    rows: list[CapitalOneBusinessCreditCardActivityRow] = []

    for raw_line in lines[fee_index + 1 :]:
        line = raw_line.strip()

        if line.startswith("Total Fees for This Period"):
            break

        if not line:
            continue

        current_match = _CURRENT_ROW_PATTERN.fullmatch(line)

        if current_match is not None:
            amount = _parse_amount(current_match.group("amount"))
            rows.append(
                CapitalOneBusinessCreditCardActivityRow(
                    transaction_date=current_match.group("transaction_date"),
                    posting_date=current_match.group("posting_date"),
                    description=current_match.group("description"),
                    amount=abs(amount),
                    section=CapitalOneBusinessCreditCardActivitySection.FEE,
                    card_last4=None,
                    raw_text=line,
                )
            )
            continue

        if _CURRENT_DATED_PREFIX_PATTERN.match(line):
            msg = (
                "Unrecognized Capital One business credit-card fee row: "
                f"{line}"
            )
            raise ValueError(msg)

        if _LEGACY_DATE_PATTERN.match(line):
            msg = (
                "Unrecognized Capital One business credit-card legacy fee "
                f"row: {line}"
            )
            raise ValueError(msg)

    return rows


def _validate_transaction_total(
    text: str,
    rows: list[CapitalOneBusinessCreditCardActivityRow],
) -> None:
    """Require parsed debits to equal the reported transaction total."""
    reported_total = _unique_reported_total(
        text,
        field="transactions",
        pattern=_TRANSACTION_TOTAL_PATTERN,
        required=False,
    )
    parsed_total = sum(
        (
            row.amount
            for row in rows
            if row.section is CapitalOneBusinessCreditCardActivitySection.DEBIT
        ),
        start=Decimal("0"),
    )

    if reported_total is None:
        if parsed_total == Decimal("0"):
            return

        msg = (
            "Capital One business credit-card transaction total was not "
            "reported for nonzero parsed activity."
        )
        raise ValueError(msg)

    if parsed_total != reported_total:
        msg = (
            "Capital One business credit-card parsed transactions do not "
            "match the reported period transaction total."
        )
        raise ValueError(msg)


def _validate_fee_total(
    text: str,
    rows: list[CapitalOneBusinessCreditCardActivityRow],
) -> None:
    """Require parsed fee rows to equal the reported fee total."""
    reported_total = _unique_reported_total(
        text,
        field="fee",
        pattern=_FEE_TOTAL_PATTERN,
        required=True,
    )
    parsed_total = sum(
        (row.amount for row in rows),
        start=Decimal("0"),
    )

    if parsed_total != reported_total:
        msg = (
            "Capital One business credit-card parsed fee rows do not match "
            "the reported period fee total."
        )
        raise ValueError(msg)


def _parse_interest_row(
    text: str,
) -> CapitalOneBusinessCreditCardActivityRow | None:
    """Parse the statement-period interest total when the product reports it."""  # noqa: E501
    is_spark = (
        _LEGACY_TITLE_MARKER in text or _SPARK_CURRENT_TITLE_MARKER in text
    )
    reported_total = _unique_reported_total(
        text,
        field="interest",
        pattern=_INTEREST_TOTAL_PATTERN,
        required=is_spark,
    )

    if reported_total in {None, Decimal("0")}:
        return None

    return CapitalOneBusinessCreditCardActivityRow(
        transaction_date=None,
        posting_date=None,
        description="INTEREST CHARGED",
        amount=reported_total,
        section=CapitalOneBusinessCreditCardActivitySection.INTEREST,
        card_last4=None,
        raw_text=f"Total Interest for This Period ${reported_total:,.2f}",
    )


def parse_activity_rows(
    text: StatementText,
) -> tuple[CapitalOneBusinessCreditCardActivityRow, ...]:
    """Parse Capital One business-card economic activity across proven eras."""
    full_text = text.text

    if _LEGACY_TITLE_MARKER in full_text:
        transaction_rows = _parse_legacy_transaction_rows(full_text)
    elif (
        _SPARK_CURRENT_TITLE_MARKER in full_text
        or _VENTURE_X_BUSINESS_TITLE_MARKER in full_text
    ):
        transaction_rows = _parse_current_transaction_rows(full_text)
    else:
        msg = "Capital One business credit-card activity layout was not recognized."  # noqa: E501
        raise ValueError(msg)

    _validate_transaction_total(
        full_text,
        transaction_rows,
    )

    fee_rows = _parse_fee_rows(full_text)
    _validate_fee_total(
        full_text,
        fee_rows,
    )

    interest_row = _parse_interest_row(full_text)

    return (
        *transaction_rows,
        *fee_rows,
        *((interest_row,) if interest_row is not None else ()),
    )
