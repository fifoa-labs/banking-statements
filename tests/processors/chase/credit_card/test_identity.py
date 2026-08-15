"""
tests/processors/chase/credit_card/test_identity.py

Tests for Chase credit-card statement identity parsing.
"""

from __future__ import annotations

from datetime import date

import pytest

from banking_statements.domain import AccountType
from banking_statements.processors.chase.credit_card.identity import (
    parse_identity,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build statement text for identity parser tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_parse_identity() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Number: XXXX XXXX XXXX 9062",
                    "Opening/Closing Date 03/12/26 - 04/11/26",
                    "Statement Date: 04/11/26",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "XXXX XXXX XXXX 9062"
    assert identity.account.last4 == "9062"
    assert identity.statement_start == date(2026, 3, 12)
    assert identity.statement_end == date(2026, 4, 11)
    assert identity.statement_date == date(2026, 4, 11)


def test_parse_identity_accepts_mangled_opening_closing_marker() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Number: 4266 8415 1445 9062",
                    "O`pening/Closing Date 12/12/20 - 01/11/21",
                    "Statement Date: 01/11/21",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "4266 8415 1445 9062"
    assert identity.account.last4 == "9062"
    assert identity.statement_start == date(2020, 12, 12)
    assert identity.statement_end == date(2021, 1, 11)
    assert identity.statement_date == date(2021, 1, 11)


def test_parse_identity_accepts_lowercase_account_number_marker() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account number: XXXX XXXX XXXX 7001",
                    "Opening/Closing Date 12/10/24 - 01/09/25",
                    "Statement Date: 01/09/25",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "XXXX XXXX XXXX 7001"
    assert identity.account.last4 == "7001"
    assert identity.statement_start == date(2024, 12, 10)
    assert identity.statement_end == date(2025, 1, 9)
    assert identity.statement_date == date(2025, 1, 9)


def test_parse_identity_requires_account_number() -> None:
    with pytest.raises(
        ValueError,
        match="account number was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Opening/Closing Date 03/12/26 - 04/11/26",
                        "Statement Date: 04/11/26",
                    )
                )
            )
        )


def test_parse_identity_requires_statement_period() -> None:
    with pytest.raises(
        ValueError,
        match="statement period was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number: XXXX XXXX XXXX 9062",
                        "Statement Date: 04/11/26",
                    )
                )
            )
        )


def test_parse_identity_requires_statement_date() -> None:
    with pytest.raises(
        ValueError,
        match="statement date was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number: XXXX XXXX XXXX 9062",
                        "Opening/Closing Date 03/12/26 - 04/11/26",
                    )
                )
            )
        )


def test_parse_identity_requires_matching_closing_date() -> None:
    with pytest.raises(
        ValueError,
        match="statement date does not match the closing date",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Account Number: XXXX XXXX XXXX 9062",
                        "Opening/Closing Date 03/12/26 - 04/11/26",
                        "Statement Date: 04/12/26",
                    )
                )
            )
        )


def test_parse_identity_accepts_unmasked_account_number() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Number: 4147 2024 9352 7244",
                    "Opening/Closing Date 12/04/23 - 01/03/24",
                    "Statement Date: 01/03/24",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "4147 2024 9352 7244"
    assert identity.account.last4 == "7244"
    assert identity.statement_start == date(2023, 12, 4)
    assert identity.statement_end == date(2024, 1, 3)
    assert identity.statement_date == date(2024, 1, 3)


def test_parse_identity_accepts_unlabeled_account_number_fallback() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    (
                        "A A A c CC cou CC nt OO Nu UU m NN ber TT : "
                        "4147 2023 1527 3936"
                    ),
                    "Opening/Closing Date 08/25/22 - 09/24/22",
                    "Statement Date: 09/24/22",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "4147 2023 1527 3936"
    assert identity.account.last4 == "3936"
    assert identity.statement_start == date(2022, 8, 25)
    assert identity.statement_end == date(2022, 9, 24)
    assert identity.statement_date == date(2022, 9, 24)


def test_parse_identity_rejects_multiple_unlabeled_account_numbers() -> None:
    with pytest.raises(
        ValueError,
        match="account number was not found uniquely",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "4147 2023 1527 3936",
                        "4266 8415 1445 9062",
                        "Opening/Closing Date 08/25/22 - 09/24/22",
                        "Statement Date: 09/24/22",
                    )
                )
            )
        )
