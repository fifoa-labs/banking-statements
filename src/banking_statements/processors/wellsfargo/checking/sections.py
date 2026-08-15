"""
src/banking_statements/processors/wellsfargo/checking/sections.py

Section extraction for supported Wells Fargo checking statements.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_statements.text import StatementText


_CHECKING_START_PATTERN = re.compile(
    r"^Wells Far\s*go .*Checking®?\s*$",
    re.MULTILINE,
)

_SAVINGS_START_PATTERN = re.compile(
    r"^Wells Far\s*go .*Savings.*$",
    re.MULTILINE,
)


def extract_checking_section(text: StatementText) -> str:
    """Return the Wells Fargo checking portion of a combined statement."""
    full_text = text.text

    checking_match = _CHECKING_START_PATTERN.search(full_text)
    if checking_match is None:
        msg = "Wells Fargo checking section was not found."
        raise ValueError(msg)

    savings_match = _SAVINGS_START_PATTERN.search(
        full_text,
        checking_match.end(),
    )

    end = (
        savings_match.start() if savings_match is not None else len(full_text)
    )

    return full_text[checking_match.start() : end]
