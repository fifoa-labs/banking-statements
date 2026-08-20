"""
tests/processors/discover/test_signatures.py

Tests for Discover institution signatures.
"""

from __future__ import annotations

from banking_statements.processors.discover import (
    DISCOVER_CHECKING_SIGNATURES,
    DISCOVER_SIGNATURES,
)


def test_discover_checking_signatures_are_stable() -> None:
    assert len(DISCOVER_CHECKING_SIGNATURES) == 3

    legacy, intermediate, current = DISCOVER_CHECKING_SIGNATURES

    assert legacy.institution == "discover"
    assert legacy.required_markers == (
        "CASHBACK CHECKING",
        "Statement Period:",
        "ACCOUNT SUMMARY",
        "Beginning Balance",
        "Ending Balance",
        "DiscoverBank.com",
    )

    assert intermediate.institution == "discover"
    assert intermediate.required_markers == (
        "CASHBACK DEBIT",
        "Statement Period:",
        "ACCOUNT SUMMARY",
        "Beginning Balance",
        "Ending Balance",
        "DiscoverBank.com",
    )

    assert current.institution == "discover"
    assert current.required_markers == (
        "CASHBACK DEBIT",
        "Statement Period:",
        "ACCOUNT SUMMARY",
        "Beginning Balance",
        "Ending Balance",
        "Discover.com",
    )


def test_discover_signatures_include_all_account_families() -> None:
    assert (*DISCOVER_CHECKING_SIGNATURES,) == DISCOVER_SIGNATURES
