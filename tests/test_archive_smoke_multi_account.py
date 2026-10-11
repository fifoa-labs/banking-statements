"""
tests/test_archive_smoke_multi_account.py

Archive validation must not overlook a secondary account mismatch.
"""

from dataclasses import replace
from decimal import Decimal

import pytest

from banking_statements.api import StatementParseResult
from banking_statements.processors.chime import ChimeCreditBuilderProcessor
from banking_statements.reconciliation import reconcile_statement
from scripts import archive_smoke
from tests.processors.chime.test_processor import CARD, SECURED, SOURCE, text


@pytest.mark.parametrize("allow_mismatch", [False, True])
def test_smoke_validates_secondary_account(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    allow_mismatch: bool,
) -> None:
    card = ChimeCreditBuilderProcessor().parse(SOURCE, text(CARD, SECURED))
    secured = card.additional_statements[0]
    secured = replace(
        secured,
        balances=replace(secured.balances, closing_balance=Decimal("1.00")),
    )
    result = StatementParseResult(
        statement=card,
        reconciliation=reconcile_statement(card),
        page_count=2,
        additional_accounts=(
            StatementParseResult(
                statement=secured,
                reconciliation=reconcile_statement(secured),
                page_count=2,
            ),
        ),
    )
    monkeypatch.setattr(archive_smoke, "parse_statement", lambda _: result)
    failures = archive_smoke.run_archive_smoke(
        (SOURCE.path,),
        start=1,
        limit=None,
        continue_on_error=False,
        show_traceback=False,
        show_transactions=True,
        allow_reconciliation_failures=allow_mismatch,
    )
    assert failures == (0 if allow_mismatch else 1)
    output = capsys.readouterr().out
    assert "account=9012" in output
    assert "difference=1.00" in output
    assert (
        "reconciliation=WARN" in output if allow_mismatch else "FAIL" in output
    )
