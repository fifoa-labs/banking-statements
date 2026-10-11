"""
src/banking_statements/processors/wellsfargo/savings/processor.py

Parse the independent savings account inside a Wells Fargo combined PDF.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from banking_statements.domain import (
    AccountType,
    ParsedStatement,
    StatementPeriod,
)
from banking_statements.processors.base import ProcessorMatch
from banking_statements.processors.wellsfargo.checking.activity import (
    parse_activity_rows,
    parse_activity_transactions,
)
from banking_statements.processors.wellsfargo.checking.identity import (
    parse_identity,
)
from banking_statements.processors.wellsfargo.checking.sections import (
    extract_savings_section,
    has_checking_section,
    has_savings_section,
)
from banking_statements.processors.wellsfargo.checking.summary import (
    parse_balance_summary,
)

if TYPE_CHECKING:
    from banking_statements.domain import StatementSource
    from banking_statements.text import StatementText


class WellsFargoSavingsProcessor:
    """Standalone selection excludes PDFs already owned by checking."""

    @property
    def name(self) -> str:
        return "wellsfargo.savings.v1"

    def match(self, text: StatementText) -> ProcessorMatch:
        matched = has_savings_section(text) and not has_checking_section(text)
        return ProcessorMatch(matched, 100 if matched else 0)

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        section = extract_savings_section(text)
        if not section.startswith("Wells Fargo Way2Save"):
            msg = "Unsupported Wells Fargo savings account family."
            raise ValueError(msg)
        identity = parse_identity(text, account_type=AccountType.SAVINGS)
        period = StatementPeriod(
            identity.statement_start, identity.statement_end
        )
        rows = parse_activity_rows(text, account_type=AccountType.SAVINGS)
        for label, values in (
            ("Deposits/Additions", (row.addition for row in rows)),
            ("Withdrawals/Subtractions", (row.subtraction for row in rows)),
        ):
            match = re.search(
                rf"{re.escape(label)}\s+(?:-\s*)?([\d,]+\.\d{{2}})",
                section,
            )
            if match is None:
                msg = "Missing Wells Fargo savings activity summary."
                raise ValueError(msg)
            reported = Decimal(match[1].replace(",", ""))
            parsed = sum(
                (value for value in values if value is not None), Decimal("0")
            )
            if reported != parsed:
                msg = (
                    "Wells Fargo savings activity does not match summary "
                    "totals."
                )
                raise ValueError(msg)
        return ParsedStatement(
            source=source,
            institution="wellsfargo",
            account=identity.account,
            processor=self.name,
            period=period,
            balances=parse_balance_summary(
                text, account_type=AccountType.SAVINGS
            ),
            transactions=parse_activity_transactions(
                rows,
                period=period,
            ),
        )
