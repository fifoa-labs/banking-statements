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
                    "Account Number: XXXX XXXX XXXX 1234",
                    "Opening/Closing Date 03/10/26 - 04/09/26",
                    "Statement Date: 04/09/26",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "XXXX XXXX XXXX 1234"
    assert identity.account.last4 == "1234"
    assert identity.statement_start == date(2026, 3, 10)
    assert identity.statement_end == date(2026, 4, 9)
    assert identity.statement_date == date(2026, 4, 9)


def test_parse_identity_accepts_mangled_opening_closing_marker() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Number: 1111 2222 3333 4444",
                    "O`pening/Closing Date 12/08/20 - 01/07/21",
                    "Statement Date: 01/07/21",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "1111 2222 3333 4444"
    assert identity.account.last4 == "4444"
    assert identity.statement_start == date(2020, 12, 8)
    assert identity.statement_end == date(2021, 1, 7)
    assert identity.statement_date == date(2021, 1, 7)


def test_parse_identity_accepts_lowercase_account_number_marker() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account number: XXXX XXXX XXXX 5678",
                    "Opening/Closing Date 11/15/24 - 12/14/24",
                    "Statement Date: 12/14/24",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "XXXX XXXX XXXX 5678"
    assert identity.account.last4 == "5678"
    assert identity.statement_start == date(2024, 11, 15)
    assert identity.statement_end == date(2024, 12, 14)
    assert identity.statement_date == date(2024, 12, 14)


def test_parse_identity_requires_account_number() -> None:
    with pytest.raises(
        ValueError,
        match="account number was not found",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "Opening/Closing Date 03/10/26 - 04/09/26",
                        "Statement Date: 04/09/26",
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
                        "Account Number: XXXX XXXX XXXX 1234",
                        "Statement Date: 04/09/26",
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
                        "Account Number: XXXX XXXX XXXX 1234",
                        "Opening/Closing Date 03/10/26 - 04/09/26",
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
                        "Account Number: XXXX XXXX XXXX 1234",
                        "Opening/Closing Date 03/10/26 - 04/09/26",
                        "Statement Date: 04/10/26",
                    )
                )
            )
        )


def test_parse_identity_accepts_unmasked_account_number() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    "Account Number: 5555 6666 7777 8888",
                    "Opening/Closing Date 12/02/23 - 01/01/24",
                    "Statement Date: 01/01/24",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "5555 6666 7777 8888"
    assert identity.account.last4 == "8888"
    assert identity.statement_start == date(2023, 12, 2)
    assert identity.statement_end == date(2024, 1, 1)
    assert identity.statement_date == date(2024, 1, 1)


def test_parse_identity_accepts_unlabeled_account_number_fallback() -> None:
    identity = parse_identity(
        make_statement_text(
            "\n".join(  # noqa: FLY002
                (
                    (
                        "A A A c CC cou CC nt OO Nu UU m NN ber TT : "
                        "2222 3333 4444 5555"
                    ),
                    "Opening/Closing Date 08/05/22 - 09/04/22",
                    "Statement Date: 09/04/22",
                )
            )
        )
    )

    assert identity.account.account_type is AccountType.CREDIT_CARD
    assert identity.account.display_number == "2222 3333 4444 5555"
    assert identity.account.last4 == "5555"
    assert identity.statement_start == date(2022, 8, 5)
    assert identity.statement_end == date(2022, 9, 4)
    assert identity.statement_date == date(2022, 9, 4)


def test_parse_identity_rejects_multiple_unlabeled_account_numbers() -> None:
    with pytest.raises(
        ValueError,
        match="account number was not found uniquely",
    ):
        parse_identity(
            make_statement_text(
                "\n".join(  # noqa: FLY002
                    (
                        "1111 2222 3333 4444",
                        "5555 6666 7777 8888",
                        "Opening/Closing Date 08/05/22 - 09/04/22",
                        "Statement Date: 09/04/22",
                    )
                )
            )
        )
