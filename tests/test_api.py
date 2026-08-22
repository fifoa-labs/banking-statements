"""
tests/test_api.py

Tests for the high-level banking statement parsing API.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from banking_statements import api
from banking_statements.domain import (
    AccountIdentity,
    AccountType,
    ParsedStatement,
    StatementBalanceSummary,
    StatementPeriod,
    StatementSource,
)
from banking_statements.processors import ProcessorMatch
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import StatementPage, StatementText


class FakeReader:
    """Synthetic statement text reader for API tests."""

    def read(self, source: StatementSource) -> StatementText:
        del source
        return StatementText(
            pages=(
                StatementPage(number=1, text="SAMPLE BANK"),
                StatementPage(number=2, text="SAMPLE ACTIVITY"),
            )
        )


class FakeDetector:
    """Synthetic institution detector for API tests."""

    def detect(self, text: StatementText) -> str:
        assert "SAMPLE BANK" in text.text
        return "sample-bank"


class FakeProcessor:
    """Synthetic statement processor for API tests."""

    @property
    def name(self) -> str:
        return "sample.credit_card.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        del text
        return ProcessorMatch(matched=True)

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        assert "SAMPLE ACTIVITY" in text.text
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
                opening_balance=Decimal("10.00"),
                closing_balance=Decimal("10.00"),
            ),
        )


class FakeRegistry:
    """Synthetic processor registry for API tests."""

    def select(self, text: StatementText) -> FakeProcessor:
        assert "SAMPLE BANK" in text.text
        return FakeProcessor()


def test_parse_statement_runs_complete_default_pipeline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statement_path = tmp_path / "statement.pdf"
    statement_path.write_bytes(b"sample-pdf-bytes")

    monkeypatch.setattr(api, "PdfStatementTextReader", FakeReader)
    monkeypatch.setattr(
        api,
        "build_default_institution_detector",
        FakeDetector,
    )
    monkeypatch.setattr(
        api,
        "build_default_processor_registry",
        FakeRegistry,
    )

    result = api.parse_statement(statement_path)

    assert result.statement.source.path == statement_path
    assert (
        result.statement.source.sha256
        == sha256(b"sample-pdf-bytes").hexdigest()
    )
    assert result.statement.institution == "sample-bank"
    assert result.statement.processor == "sample.credit_card.v1"
    assert result.page_count == 2
    assert result.reconciliation.reconciled is True
    assert result.reconciliation.difference == Decimal("0.00")


def test_parse_statement_accepts_string_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statement_path = tmp_path / "statement.pdf"
    statement_path.write_bytes(b"sample")

    monkeypatch.setattr(api, "PdfStatementTextReader", FakeReader)
    monkeypatch.setattr(
        api,
        "build_default_institution_detector",
        FakeDetector,
    )
    monkeypatch.setattr(
        api,
        "build_default_processor_registry",
        FakeRegistry,
    )

    result = api.parse_statement(str(statement_path))

    assert result.statement.source.path == statement_path


def test_parse_statements_recursively_discovers_pdfs_in_path_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "a.pdf"
    second = tmp_path / "nested" / "b.PDF"
    ignored = tmp_path / "nested" / "notes.txt"

    second.parent.mkdir()
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    ignored.write_text("not a statement")

    seen: list[Path] = []

    def fake_parse_statement(path: str | Path) -> api.StatementParseResult:
        statement_path = Path(path)
        seen.append(statement_path)

        statement = ParsedStatement(
            source=StatementSource(
                path=statement_path,
                sha256="0" * 64,
            ),
            institution="sample-bank",
            account=AccountIdentity(
                account_type=AccountType.CREDIT_CARD,
                display_number="1234",
                last4="1234",
            ),
            processor="sample.credit_card.v1",
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
            balances=StatementBalanceSummary(
                opening_balance=Decimal("0.00"),
                closing_balance=Decimal("0.00"),
            ),
        )

        return api.StatementParseResult(
            statement=statement,
            reconciliation=reconcile_statement(statement),
            page_count=1,
        )

    monkeypatch.setattr(api, "parse_statement", fake_parse_statement)

    results = api.parse_statements(tmp_path)

    assert seen == [first, second]
    assert tuple(result.statement.source.path for result in results) == (
        first,
        second,
    )


def test_parse_statements_accepts_one_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statement_path = tmp_path / "anything.bin"
    statement_path.write_bytes(b"sample")

    seen: list[Path] = []

    def fake_parse_statement(path: str | Path) -> api.StatementParseResult:
        statement = ParsedStatement(
            source=StatementSource(
                path=Path(path),
                sha256="0" * 64,
            ),
            institution="sample",
            account=AccountIdentity(
                account_type=AccountType.CHECKING,
                display_number="1234",
                last4="1234",
            ),
            processor="sample.checking.v1",
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
            balances=StatementBalanceSummary(
                opening_balance=Decimal("0.00"),
                closing_balance=Decimal("0.00"),
            ),
        )
        seen.append(statement.source.path)
        return api.StatementParseResult(
            statement=statement,
            reconciliation=reconcile_statement(statement),
            page_count=1,
        )

    monkeypatch.setattr(api, "parse_statement", fake_parse_statement)

    results = api.parse_statements(statement_path)

    assert len(results) == 1
    assert seen == [statement_path]


def test_parse_statements_rejects_missing_source(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(
        ValueError,
        match="statement source does not exist",
    ):
        api.parse_statements(missing)
