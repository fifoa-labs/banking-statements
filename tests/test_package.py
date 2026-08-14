"""
tests/test_package.py

Tests for the public banking_statements package.
"""

from __future__ import annotations

import banking_statements


def test_package_version() -> None:
    assert banking_statements.__version__ == "0.1.0"
