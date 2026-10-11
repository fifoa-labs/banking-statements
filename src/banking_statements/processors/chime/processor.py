"""
src/banking_statements/processors/chime/processor.py

Known Chime checking and combined Credit Builder document grammars.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, NoReturn

from banking_statements.domain import (
    AccountIdentity,
    AccountType,
    ParsedStatement,
    SourceEvidence,
    StatementBalanceSummary,
    StatementPeriod,
    TransactionDirection,
    TransactionEvent,
)
from banking_statements.exceptions import UnsupportedStatementError
from banking_statements.processors.base import ProcessorMatch

from .signatures import CARD_TITLE, CHECKING_TITLE, SECURED_TITLE

if TYPE_CHECKING:
    from banking_statements.domain import StatementSource
    from banking_statements.text import StatementText

_MONEY = r"-?\$[\d,]+\.\d{2}"
_DATE = r"\d{1,2}/\d{1,2}/\d{4}"
_PERIOD = re.compile(r"Statement period\n[^\n]+ \((.+?) - (.+?)\)")
_ROW = re.compile(
    rf"^({_DATE}) (.+) (Transfer|Deposit) "
    rf"({_MONEY})(?: ({_MONEY}))? ({_DATE})$"
)


def _fail(message: str) -> NoReturn:
    raise UnsupportedStatementError(message)


def _money(value: str) -> Decimal:
    return Decimal(value.replace("$", "").replace(",", ""))


def _balance(text: str, label: str) -> Decimal:
    matches = re.findall(rf"^{label} ({_MONEY})(?: .*|$)", text, re.M)
    if len(matches) != 1:
        _fail(f"Chime requires exactly one {label} balance.")
    return _money(matches[0])


def _period(text: str) -> StatementPeriod:
    match = _PERIOD.search(text)
    if match is None:
        _fail("Missing Chime statement period.")
    dates = tuple(
        datetime.strptime(
            re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", value),
            "%B %d, %Y",
        )
        .replace(tzinfo=UTC)
        .date()
        for value in match.groups()
    )
    if dates[0] > dates[1]:
        _fail("Reversed Chime statement period.")
    return StatementPeriod(start=dates[0], end=dates[1])


def _identity(text: str, account_type: AccountType) -> AccountIdentity:
    match = re.search(r"Account number[^\n]*\n(\d+)(?: |\n)", text)
    if match is None:
        _fail("Missing Chime account number.")
    number = match[1]
    return AccountIdentity(account_type, number, number[-4:])


def _activity_lines(
    text: StatementText,
    title: str,
) -> tuple[tuple[int, str], ...]:
    """Locate only the selected account's transaction table across pages."""
    lines: list[tuple[int, str]] = []
    in_account = False
    active = False
    for page in text.pages:
        for line in page.text.splitlines():
            if line == title:
                in_account = True
            if not in_account:
                continue
            if line == "Transactions":
                active = True
                continue
            if not active or not line or line.startswith("Page "):
                continue
            if line in ("Yearly Summary", "Error Resolution Procedures") or (
                line.startswith("TOTAL FOR THIS PERIOD:")
            ):
                return tuple(lines)
            if not line.startswith("TRANSACTION DATE DESCRIPTION TYPE AMOUNT"):
                lines.append((page.number, line))
    if not active:
        _fail("Missing Chime Transactions section.")
    _fail("Missing Chime transaction table boundary.")


def _transaction(
    match: re.Match[str],
    *,
    title: str,
    period: StatementPeriod,
    evidence: SourceEvidence,
) -> TransactionEvent:
    """Validate a known signed row and retain both dates in source evidence."""
    transaction_date, description, _, amount, net, settlement = match.groups()
    if (title == CHECKING_TITLE) != (net is not None):
        _fail("Unexpected Chime amount columns.")
    value = _money(amount)
    if net is not None and value != _money(net):
        _fail("Unsupported Chime amount/net amount difference.")
    date = (
        datetime.strptime(transaction_date, "%m/%d/%Y")
        .replace(
            tzinfo=UTC,
        )
        .date()
    )
    datetime.strptime(settlement, "%m/%d/%Y").replace(tzinfo=UTC)
    if not period.start <= date <= period.end:
        _fail("Chime transaction outside statement period.")
    return TransactionEvent(
        date=date,
        amount=abs(value),
        direction=(
            TransactionDirection.DEBIT
            if value < 0
            else TransactionDirection.CREDIT
        ),
        description=description,
        evidence=evidence,
    )


def _activity(
    source: StatementSource,
    text: StatementText,
    *,
    title: str,
    period: StatementPeriod,
    processor: str,
) -> tuple[TransactionEvent, ...]:
    transactions: list[TransactionEvent] = []
    for page, line in _activity_lines(text, title):
        match = _ROW.fullmatch(line)
        if match is None:
            if re.match(r"\d{1,2}/", line) or "$" in line:
                _fail("Unsupported Chime activity row.")
            if not transactions:
                _fail("Orphan Chime description continuation.")
            previous = transactions[-1]
            assert previous.evidence is not None
            transactions[-1] = replace(
                previous,
                description=f"{previous.description} {line}",
                evidence=replace(
                    previous.evidence,
                    raw_text=f"{previous.evidence.raw_text}\n{line}",
                ),
            )
            continue
        transactions.append(
            _transaction(
                match,
                title=title,
                period=period,
                evidence=SourceEvidence(
                    source=source,
                    page=page,
                    section=title + " / Transactions",
                    raw_text=line,
                    processor=processor,
                    sequence=len(transactions) + 1,
                ),
            )
        )
    return tuple(transactions)


def _deposit_statement(
    source: StatementSource,
    text: StatementText,
    *,
    title: str,
    processor: str,
) -> ParsedStatement:
    body = text.text.split(title, 1)[1]
    period = _period(body)
    return ParsedStatement(
        source=source,
        institution="chime",
        account=_identity(body, AccountType.CHECKING),
        processor=processor,
        period=period,
        balances=StatementBalanceSummary(
            opening_balance=_balance(body, r"Beginning balance on [^$]+"),
            closing_balance=_balance(body, r"Ending balance on [^$]+"),
        ),
        transactions=_activity(
            source,
            text,
            title=title,
            period=period,
            processor=processor,
        ),
    )


class ChimeCheckingProcessor:
    """Checking grammar evidenced by the supplied monthly statements."""

    @property
    def name(self) -> str:
        return "chime.checking.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        matched = CHECKING_TITLE in text.text and "Chime" in text.text
        return ProcessorMatch(matched, 100 if matched else 0)

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        return _deposit_statement(
            source,
            text,
            title=CHECKING_TITLE,
            processor=self.name,
        )


class ChimeCreditBuilderProcessor:
    """Inactive card plus independently reconciled secured deposit account."""

    @property
    def name(self) -> str:
        return "chime.credit_builder.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        matched = CARD_TITLE in text.text and "Chime" in text.text
        return ProcessorMatch(matched, 100 if matched else 0)

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        if text.text.count(SECURED_TITLE) != 1:
            _fail("Chime Credit Builder requires its secured account section.")
        card = text.text.split(SECURED_TITLE, 1)[0]
        for label in (
            "Previous Balance",
            "Payments/Credits",
            "New spending",
            "Fees",
            "New balance",
        ):
            if _balance(card, re.escape(label)) != 0:
                _fail(
                    "Active Chime card activity requires new source evidence."
                )
        # Each observed card table is empty. Never ignore an active row,
        # even if its effects cancel and the summary remains zero.
        for section in (
            "Payments",
            "Transactions",
            "Fees",
            "Disputed transactions",
        ):
            pattern = (
                rf"\n{section}\nTRANSACTION DATE DESCRIPTION TYPE AMOUNT "
                rf"SETTLEMENT DATE\nTOTAL FOR THIS PERIOD: ({_MONEY})"
            )
            match = re.search(pattern, card)
            if match is None or _money(match[1]) != 0:
                _fail("Unsupported Chime card activity table.")
        secured = _deposit_statement(
            source,
            text,
            title=SECURED_TITLE,
            processor="chime.secured_account.v1",
        )
        return ParsedStatement(
            source=source,
            institution="chime",
            account=_identity(card, AccountType.CREDIT_CARD),
            processor=self.name,
            period=_period(card),
            balances=StatementBalanceSummary(Decimal("0"), Decimal("0")),
            additional_statements=(secured,),
        )
