"""
tests/processors/chase/credit_card/test_processor.py

Tests for the Chase credit-card statement processor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from banking_statements.domain import StatementSource
from banking_statements.processors.chase import ChaseCreditCardProcessor
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
    processor = ChaseCreditCardProcessor()

    assert processor.name == "chase.credit_card.v1"


def test_processor_matches_supported_structure() -> None:
    processor = ChaseCreditCardProcessor()

    text = make_statement_text(
        "\n".join(  # noqa: FLY002
            (
                "www.chase.com/cardhelp",
                "Account Number: XXXX XXXX XXXX 1234",
                "Opening/Closing Date 01/01/26 - 01/31/26",
                "Date of",
                "Transaction Merchant Name or Transaction Description $ Amount",  # noqa: E501
            )
        )
    )

    match = processor.match(text)

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == "Matched Chase credit-card statement structure."


def test_processor_rejects_unsupported_structure() -> None:
    processor = ChaseCreditCardProcessor()

    match = processor.match(
        make_statement_text("Not a Chase credit-card statement"),
    )

    assert match.matched is False
    assert match.confidence == 0
    assert match.reason == (
        "Required Chase credit-card markers were not found."
    )


def test_processor_stops_at_identity_boundary() -> None:
    processor = ChaseCreditCardProcessor()

    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    with pytest.raises(
        NotImplementedError,
        match="Chase credit-card identity parsing is not implemented",
    ):
        processor.parse(
            source,
            make_statement_text("statement"),
        )
