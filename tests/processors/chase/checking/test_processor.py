"""
tests/processors/chase/checking/test_processor.py

Tests for the Chase checking statement processor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from banking_statements.domain import StatementSource
from banking_statements.processors.chase import ChaseCheckingProcessor
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for processor tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_processor_name_is_stable() -> None:
    processor = ChaseCheckingProcessor()

    assert processor.name == "chase.checking.v1"


def test_processor_matches_supported_structure() -> None:
    processor = ChaseCheckingProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "JPMorgan Chase Bank, N.A.",
                "CHECKING SUMMARY Chase Total Checking",
                "TRANSACTION DETAIL",
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == "Matched Chase checking statement structure."


def test_processor_rejects_unsupported_structure() -> None:
    processor = ChaseCheckingProcessor()

    match = processor.match(
        make_statement_text("Not a Chase checking statement"),
    )

    assert match.matched is False
    assert match.confidence == 0
    assert match.reason == ("Required Chase checking markers were not found.")


def test_processor_parse_reaches_balance_summary_boundary() -> None:
    processor = ChaseCheckingProcessor()

    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "January 1, 2026 through January 31, 2026",
                "JPMorgan Chase Bank, N.A.",
                "Account Number: 000000000001234",
                "CHECKING SUMMARY Chase Total Checking",
                "TRANSACTION DETAIL",
            )
        )
    )

    with pytest.raises(
        NotImplementedError,
        match=(
            "Chase checking balance summary parsing is not implemented yet."  # noqa: RUF043
        ),
    ):
        processor.parse(source, text)
