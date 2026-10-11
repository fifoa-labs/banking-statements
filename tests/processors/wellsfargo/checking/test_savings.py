"""Synthetic coverage for independent Wells Fargo savings accounts."""

from decimal import Decimal

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.wellsfargo.checking.sections import (
    extract_savings_section,
)
from banking_statements.processors.wellsfargo.savings import (
    WellsFargoSavingsProcessor,
)
from banking_statements.text import StatementText
from tests.processors.wellsfargo.checking.test_processor import (
    make_source,
    make_statement_text,
    make_word,
)


def savings_text(
    *, deposits: str = "25.00", header: str = "ctions"
) -> StatementText:
    """Build unrelated, synthetic savings evidence with split header."""
    return make_statement_text(
        "Wells Fargo Way2Save Savings\n"
        "Activity summary Account number: 111122223333\n"
        "Beginning balance on 12/14 $100.00\n"
        f"Deposits/Additions {deposits}\n"
        "Withdrawals/Subtractions - 5.00\n"
        "Ending balance on 1/14 $120.00\n"
        "Fee period 12/14/2018 - 01/14/2019\n",
        words=(
            make_word("Wells Fargo Way2Save Savings", x0=40, top=10),
            make_word("Transaction history", x0=40, top=20),
            make_word("Additions", x0=397, top=30),
            make_word(header, x0=479, top=30),
            make_word("balance", x0=537, top=30),
            make_word("12/20", x0=40, top=40),
            make_word("Transfer From Checking", x0=100, top=40),
            make_word("25.00", x0=410, top=40),
            make_word("125.00", x0=540, top=40),
            make_word("1/5", x0=40, top=50),
            make_word("Withdrawal", x0=100, top=50),
            make_word("5.00", x0=480, top=50),
            make_word("120.00", x0=540, top=50),
        ),
    )


@pytest.mark.parametrize("header", ["ctions", "Subtractions"])
def test_savings_parse(header: str) -> None:
    processor = WellsFargoSavingsProcessor()
    text = savings_text(header=header)
    assert processor.match(text).matched
    result = processor.parse(make_source(), text)
    assert result.processor == "wellsfargo.savings.v1"
    assert result.account.account_type is AccountType.SAVINGS
    assert result.account.last4 == "3333"
    assert result.balances.closing_balance == Decimal("120")
    assert [row.amount for row in result.transactions] == [
        Decimal("25"),
        Decimal("5"),
    ]


def test_savings_match_excludes_combined() -> None:
    processor = WellsFargoSavingsProcessor()
    assert not processor.match(make_statement_text("Other bank")).matched
    assert not processor.match(
        make_statement_text(
            "Wells Fargo Everyday Checking\nWells Fargo Way2Save Savings\n"
        )
    ).matched


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("Other bank", "was not found"),
        (
            "Wells Fargo Way2Save Savings\nWells Fargo Way2Save Savings\n",
            "Multiple",
        ),
    ],
)
def test_savings_section_errors(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        extract_savings_section(make_statement_text(text))


def test_unsupported_family() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        WellsFargoSavingsProcessor().parse(
            make_source(), make_statement_text("Wells Fargo Other Savings\n")
        )


@pytest.mark.parametrize(
    ("deposits", "message"),
    [
        ("20.00", "does not match"),
        ("unavailable", "Missing"),
    ],
)
def test_activity_totals_guard(deposits: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        WellsFargoSavingsProcessor().parse(
            make_source(), savings_text(deposits=deposits)
        )


def test_combined_returns_independent_savings() -> None:
    from banking_statements.processors.wellsfargo.checking import (  # noqa: PLC0415
        WellsFargoCheckingProcessor,
    )
    from banking_statements.text import StatementPage  # noqa: PLC0415

    checking = make_statement_text(
        "Wells Fargo Everyday Checking\n"
        "Activity summary Account number: 444455556666\n"
        "Beginning balance on 12/14 $50.00\n"
        "Deposits/Additions 0.00\n"
        "Withdrawals/Subtractions - 0.00\n"
        "Ending balance on 1/14 $50.00\n"
        "Fee period 12/14/2018 - 01/14/2019\n",
        words=(make_word("Wells Fargo Everyday Checking", x0=40, top=10),),
    )
    savings = savings_text().pages[0]
    combined = StatementText(
        pages=(
            checking.pages[0],
            StatementPage(number=2, text=savings.text, words=savings.words),
        )
    )
    result = WellsFargoCheckingProcessor().parse(make_source(), combined)
    assert result.account.last4 == "6666"
    assert result.transactions == ()
    assert len(result.additional_statements) == 1
    secondary = result.additional_statements[0]
    assert secondary.account.last4 == "3333"
    assert secondary.account.account_type is AccountType.SAVINGS
    assert len(secondary.transactions) == 2


def test_savings_summary_row_is_not_a_section() -> None:
    summary = "Wells Fargo Way2Save® Savings 3 111122223333 100.00 120.00\n"
    detail = savings_text().text
    text = make_statement_text(summary + detail)
    assert extract_savings_section(text) == detail
    assert (
        not WellsFargoSavingsProcessor()
        .match(make_statement_text(summary))
        .matched
    )
