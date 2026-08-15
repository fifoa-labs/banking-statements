"""
tests/processors/test_registry.py

Tests for deterministic processor selection.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from banking_statements.domain import (
    AccountIdentity,
    AccountType,
    ParsedStatement,
    StatementBalanceSummary,
    StatementPeriod,
    StatementSource,
)
from banking_statements.exceptions import (
    AmbiguousProcessorError,
    UnsupportedStatementError,
)
from banking_statements.processors import (
    ProcessorMatch,
    ProcessorRegistry,
)
from banking_statements.text import StatementText


class FakeProcessor:
    """Minimal processor used to exercise registry behavior."""

    def __init__(self, name: str, *, matched: bool) -> None:
        self._name = name
        self._matched = matched

    @property
    def name(self) -> str:
        return self._name

    def match(self, text: StatementText) -> ProcessorMatch:
        del text
        return ProcessorMatch(matched=self._matched)

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        del text
        return ParsedStatement(
            source=source,
            institution="sample-bank",
            account=AccountIdentity(
                account_type=AccountType.CREDIT_CARD,
                display_number="XXXX XXXX XXXX 1234",
                last4="1234",
            ),
            processor=self.name,
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
            balances=StatementBalanceSummary(
                opening_balance=Decimal("0.00"),
                closing_balance=Decimal("0.00"),
            ),
        )


def test_registry_exposes_registered_processors() -> None:
    processor = FakeProcessor("sample", matched=True)
    registry = ProcessorRegistry([processor])

    assert registry.processors == (processor,)


def test_registry_selects_exactly_one_match() -> None:
    expected = FakeProcessor("expected", matched=True)
    registry = ProcessorRegistry(
        [
            FakeProcessor("other", matched=False),
            expected,
        ]
    )

    selected = registry.select(StatementText(pages=()))

    assert selected is expected


def test_registry_rejects_no_matches() -> None:
    registry = ProcessorRegistry([FakeProcessor("sample", matched=False)])

    with pytest.raises(UnsupportedStatementError):
        registry.select(StatementText(pages=()))


def test_registry_rejects_multiple_matches() -> None:
    registry = ProcessorRegistry(
        [
            FakeProcessor("first", matched=True),
            FakeProcessor("second", matched=True),
        ]
    )

    with pytest.raises(
        AmbiguousProcessorError,
        match="first, second",
    ):
        registry.select(StatementText(pages=()))
