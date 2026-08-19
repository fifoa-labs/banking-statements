"""
src/banking_statements/processors/american_express/credit_card/activity/rows.py

Logical activity-row reconstruction for American Express
credit-card statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


class AmericanExpressCreditCardActivitySection(StrEnum):
    """Supported American Express credit-card activity sections."""

    PAYMENTS = "payments"
    CREDITS = "credits"
    CHARGES = "charges"
    FEES = "fees"
    INTEREST = "interest"


@dataclass(frozen=True, slots=True)
class AmericanExpressCreditCardActivityRow:
    """One reconstructed American Express credit-card activity row."""

    section: AmericanExpressCreditCardActivitySection
    date_text: str | None
    description: str
    amount_text: str
    card_ending: str | None = None
    date_is_posting: bool = False
    continuation_lines: tuple[str, ...] = ()
    raw_text: str | None = None


_DATE_ROW_PATTERN = re.compile(
    r"^(?P<leading_star>\*)?"
    r"(?P<date>\d{2}/\d{2}/\d{2})"
    r"(?P<trailing_star>\*)?\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>[+-]?\$?[\d,]+\.\d{2})"
    r"(?P<credit>\s+CR)?"
    r"(?P<pay_over_time>[t⧫])?$",
)

_DATE_PREFIX_PATTERN = re.compile(
    r"^\*?\d{2}/\d{2}/\d{2}\*?\b",
)

_DETAIL_DATE_PAIR_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{2}\s+\d{2}/\d{2}/\d{2}$",
)

_UNDATED_AMOUNT_PATTERN = re.compile(
    r"^(?P<description>.+?)\s+"
    r"(?P<amount>[+-]?\$?[\d,]+\.\d{2})"
    r"(?P<credit>\s+CR)?$",
)

_CARD_ENDING_PATTERN = re.compile(
    r"^Card Ending\s*(?P<ending>\d-\d{5})$",
)

_YEAR_TOTALS_PATTERN = re.compile(
    r"^\d{4} Fees and Interest Totals Year-to-Date$",
)

_DETAIL_MARKERS = (
    "Detail",
    "Detail *Indicates posting date",
    "Detail *Indicates posting date - denotes Pay Over Time activity",
    (
        "Detail *Indicates posting date - denotes Pay Over Time and/or "
        "Cash Advance activity"
    ),
    "Detail *Indicates posting date ⧫ - Pay Over Time activity",
    (
        "Detail *Indicates posting date ⧫ - denotes Pay Over Time and/or "
        "Cash Advance activity"
    ),
    (
        "Detail *Indicates posting date ⧫ - Pay Over Time and/or "
        "Cash Advance activity"
    ),
    "Detail - denotes Pay Over Time activity",
    "Detail - denotes Pay Over Time and/or Cash Advance activity",
    "Detail ⧫ - Pay Over Time activity",
    "Detail ⧫ - denotes Pay Over Time and/or Cash Advance activity",
    "Detail ⧫ - Pay Over Time and/or Cash Advance activity",
    "Detail Continued",
    "Detail Continued *Indicates posting date",
    "Detail Continued *Indicates posting date ⧫ - Pay Over Time activity",
    "Detail Continued - denotes Pay Over Time activity",
    "Detail Continued - denotes Pay Over Time and/or Cash Advance activity",
    "Detail Continued ⧫ - Pay Over Time activity",
    (
        "Detail Continued ⧫ - denotes Pay Over Time and/or Cash Advance "
        "activity"
    ),
    "Detail Continued ⧫ - Pay Over Time and/or Cash Advance activity",
)

_IGNORED_LINES = frozenset(
    {
        "Summary",
        "Total",
        "Amount",
        "Description Price",
        "Continued on reverse",
    }
)


def _with_credit_suffix(amount: str, credit: str | None) -> str:
    """Preserve an American Express CR suffix with an amount token."""
    if credit is None:
        return amount

    return f"{amount} CR"


def _append_continuation(
    row: AmericanExpressCreditCardActivityRow,
    line: str,
) -> AmericanExpressCreditCardActivityRow:
    """Return an activity row with one additional continuation line."""
    return replace(
        row,
        continuation_lines=(
            *row.continuation_lines,
            line,
        ),
    )


def _is_page_structure(line: str) -> bool:
    """Return whether a line is repeated statement/page structure."""
    return (
        "Account Ending" in line
        or "Closing Date" in line
        or line.startswith("p. ")
    )


def _is_stop_marker(line: str) -> bool:
    """Return whether a line ends a financial activity section."""
    return (
        line.startswith(
            (
                "Total Payments and Credits",
                "Total Fees for this Period",
                "Total Interest Charged for this Period",
                "Interest Charge Calculation",
            )
        )
        or _YEAR_TOTALS_PATTERN.fullmatch(line) is not None
    )


def _section_marker(
    line: str,
) -> AmericanExpressCreditCardActivitySection | None:
    """Return a direct activity-section marker when present."""
    if line in {"Payments", "Payments Amount"} or line.startswith(
        "Payments americanexpress.com/"
    ):
        return AmericanExpressCreditCardActivitySection.PAYMENTS

    if line in {"Credits", "Credits Amount"}:
        return AmericanExpressCreditCardActivitySection.CREDITS

    if line == "Fees":
        return AmericanExpressCreditCardActivitySection.FEES

    if line == "Interest Charged":
        return AmericanExpressCreditCardActivitySection.INTEREST

    if line in _DETAIL_MARKERS:
        return AmericanExpressCreditCardActivitySection.CHARGES

    return None


def _build_dated_row(
    match: re.Match[str],
    *,
    section: AmericanExpressCreditCardActivitySection,
    card_ending: str | None,
    raw_text: str,
) -> AmericanExpressCreditCardActivityRow:
    """Build one dated American Express activity row."""
    return AmericanExpressCreditCardActivityRow(
        section=section,
        date_text=match.group("date"),
        description=match.group("description"),
        amount_text=_with_credit_suffix(
            match.group("amount"),
            match.group("credit"),
        ),
        card_ending=card_ending,
        date_is_posting=(
            match.group("leading_star") is not None
            or match.group("trailing_star") is not None
        ),
        raw_text=raw_text,
    )


def _build_undated_row(
    match: re.Match[str],
    *,
    section: AmericanExpressCreditCardActivitySection,
    raw_text: str,
) -> AmericanExpressCreditCardActivityRow:
    """Build one undated fee or interest activity row."""
    return AmericanExpressCreditCardActivityRow(
        section=section,
        date_text=None,
        description=match.group("description"),
        amount_text=_with_credit_suffix(
            match.group("amount"),
            match.group("credit"),
        ),
        raw_text=raw_text,
    )


def parse_activity_rows(  # noqa: C901, PLR0912, PLR0915
    text: StatementText,
) -> tuple[AmericanExpressCreditCardActivityRow, ...]:
    """Reconstruct American Express credit-card activity rows."""
    rows: list[AmericanExpressCreditCardActivityRow] = []
    section: AmericanExpressCreditCardActivitySection | None = None
    card_ending: str | None = None
    pending_row: AmericanExpressCreditCardActivityRow | None = None

    def flush_pending() -> None:
        nonlocal pending_row

        if pending_row is not None:
            rows.append(pending_row)
            pending_row = None

    for raw_line in text.text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line == "Payments and Credits":
            flush_pending()
            section = None
            card_ending = None
            continue

        if line == "New Charges":
            flush_pending()
            section = None
            card_ending = None
            continue

        discovered_section = _section_marker(line)
        if discovered_section is not None:
            flush_pending()
            section = discovered_section

            if section is not AmericanExpressCreditCardActivitySection.CHARGES:
                card_ending = None

            continue

        card_match = _CARD_ENDING_PATTERN.fullmatch(line)
        if card_match is not None:
            flush_pending()
            card_ending = card_match.group("ending")
            continue

        if section is None:
            continue

        if _is_stop_marker(line):
            flush_pending()
            section = None
            card_ending = None
            continue

        if line in _IGNORED_LINES or _is_page_structure(line):
            continue

        dated_match = _DATE_ROW_PATTERN.fullmatch(line)
        if dated_match is not None:
            flush_pending()
            pending_row = _build_dated_row(
                dated_match,
                section=section,
                card_ending=card_ending,
                raw_text=line,
            )
            continue

        if pending_row is not None and _DETAIL_DATE_PAIR_PATTERN.fullmatch(
            line
        ):
            pending_row = _append_continuation(
                pending_row,
                line,
            )
            continue

        if _DATE_PREFIX_PATTERN.match(line):
            msg = (
                "Unrecognized American Express credit-card transaction row: "
                f"{line}"
            )
            raise ValueError(msg)

        if section in {
            AmericanExpressCreditCardActivitySection.FEES,
            AmericanExpressCreditCardActivitySection.INTEREST,
        }:
            undated_match = _UNDATED_AMOUNT_PATTERN.fullmatch(line)
            if undated_match is not None:
                flush_pending()
                pending_row = _build_undated_row(
                    undated_match,
                    section=section,
                    raw_text=line,
                )
                continue

        if pending_row is not None:
            pending_row = _append_continuation(
                pending_row,
                line,
            )

    flush_pending()
    return tuple(rows)
