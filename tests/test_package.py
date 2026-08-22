"""
tests/test_package.py

Tests for the public banking_statements package.
"""

from __future__ import annotations

from importlib.metadata import version

import banking_statements


def test_package_version_matches_distribution_metadata() -> None:
    assert banking_statements.__version__ == version("banking-statements")


def test_package_exports_high_level_parsing_api() -> None:
    assert banking_statements.StatementParseResult is not None
    assert banking_statements.parse_statement is not None
    assert banking_statements.parse_statements is not None
