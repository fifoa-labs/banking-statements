"""
scripts/archive_smoke.py

Run private banking statement PDFs through the supported processing pipeline.

Examples:

    Run the full Chase credit-card archive and stop on the first failure:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card

    Run one statement:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card/20260803-statements-7244-.pdf

    Run one statement and print normalized transactions:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card/20260803-statements-7244-.pdf \
            --show-transactions

    Process only the first 10 statements:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card \
            --limit 10

    Continue through parser or reconciliation failures:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card \
            --continue-on-error

    Show tracebacks for parser failures:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card \
            --traceback

    Allow reconciliation mismatches without failing the smoke run:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card \
            --allow-reconciliation-failures

    Inspect all statements while allowing reconciliation mismatches:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card \
            --continue-on-error \
            --allow-reconciliation-failures

    Inspect all statements, allow reconciliation mismatches, and print every
    normalized transaction:

        uv run python -m scripts.archive_smoke \
            private-data/statements/chase/credit-card \
            --continue-on-error \
            --allow-reconciliation-failures \
            --show-transactions

By default, both parsing failures and reconciliation mismatches cause the smoke
run to fail. Reconciliation remains diagnostic only in the library itself;
the strict behavior belongs to this development smoke tool.
"""  # noqa: E501

from __future__ import annotations

import argparse
import traceback
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from banking_statements.domain import StatementSource
from banking_statements.processors import (
    build_default_institution_detector,
    build_default_processor_registry,
)
from banking_statements.reconciliation import reconcile_statement
from banking_statements.text import PdfStatementTextReader

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.domain import ParsedStatement
    from banking_statements.reconciliation import StatementReconciliation


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run private banking statement PDFs through banking-statements."
        ),
    )
    parser.add_argument(
        "source",
        type=Path,
        help="PDF file or directory containing statement PDFs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only the first N discovered statements.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing after a statement fails.",
    )
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Show Python tracebacks for failures.",
    )
    parser.add_argument(
        "--show-transactions",
        action="store_true",
        help="Print normalized transactions for each parsed statement.",
    )
    parser.add_argument(
        "--allow-reconciliation-failures",
        action="store_true",
        help=(
            "Report reconciliation mismatches without treating them "
            "as smoke failures."
        ),
    )
    return parser


def discover_statements(
    source: Path,
) -> tuple[Path, ...]:
    """Return statement PDFs in deterministic path order."""
    if source.is_file():
        return (source,)

    if not source.is_dir():
        msg = f"statement source does not exist: {source}"
        raise ValueError(msg)

    return tuple(
        sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.casefold() == ".pdf"
        )
    )


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest for a statement file."""
    digest = sha256()

    with path.open("rb") as source_file:
        while chunk := source_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def run_archive_smoke(
    statements: Sequence[Path],
    *,
    continue_on_error: bool,
    show_traceback: bool,
    show_transactions: bool,
    allow_reconciliation_failures: bool,
) -> int:
    """Parse statements and return the number of smoke failures."""
    reader = PdfStatementTextReader()
    detector = build_default_institution_detector()
    registry = build_default_processor_registry()

    failures = 0
    total = len(statements)

    for index, path in enumerate(
        statements,
        start=1,
    ):
        label = f"[{index:02d}/{total:02d}]"

        try:
            source = StatementSource(
                path=path,
                sha256=file_sha256(path),
            )
            text = reader.read(source)

            detector.detect(text)

            processor = registry.select(text)
            statement = processor.parse(
                source,
                text,
            )
            reconciliation = reconcile_statement(statement)
        except Exception as exc:  # noqa: BLE001
            failures += 1

            print(f"{label} FAIL {path}")  # noqa: T201
            print(  # noqa: T201
                f"         {type(exc).__name__}: {exc}",
            )

            if show_traceback:
                traceback.print_exc()

            if not continue_on_error:
                break

            continue

        if not reconciliation.reconciled and not allow_reconciliation_failures:
            failures += 1

            _print_failure(
                label,
                path,
                statement=statement,
                reconciliation=reconciliation,
                page_count=len(text.pages),
                show_transactions=show_transactions,
            )

            if not continue_on_error:
                break

            continue

        _print_success(
            label,
            path,
            statement=statement,
            reconciliation=reconciliation,
            page_count=len(text.pages),
            show_transactions=show_transactions,
            reconciliation_is_warning=allow_reconciliation_failures,
        )

    return failures


def _print_statement_details(
    *,
    statement: ParsedStatement,
    page_count: int,
) -> None:
    """Print normalized statement details shared by PASS and FAIL output."""
    print(  # noqa: T201
        "         "
        f"institution={statement.institution} "
        f"processor={statement.processor} "
        f"pages={page_count}",
    )
    print(  # noqa: T201
        "         "
        f"type={statement.account.account_type.value} "
        f"period={statement.period.start.isoformat()}"
        ".."
        f"{statement.period.end.isoformat()} "
        f"account={statement.account.last4}",
    )
    print(  # noqa: T201
        "         "
        f"opening_balance={statement.balances.opening_balance} "
        f"closing_balance={statement.balances.closing_balance}",
    )
    print(  # noqa: T201
        f"         transactions={len(statement.transactions)}",
    )


def _print_transactions(
    statement: ParsedStatement,
) -> None:
    """Print normalized transactions from a parsed statement."""
    for transaction in statement.transactions:
        print(  # noqa: T201
            "         "
            f"{transaction.date.isoformat()} "
            f"{transaction.direction.value} "
            f"{transaction.amount} "
            f"{transaction.description}",
        )


def _print_success(  # noqa: PLR0913
    label: str,
    path: Path,
    *,
    statement: ParsedStatement,
    reconciliation: StatementReconciliation,
    page_count: int,
    show_transactions: bool,
    reconciliation_is_warning: bool,
) -> None:
    """Print a successful normalized statement summary."""
    print(f"{label} PASS {path}")  # noqa: T201

    _print_statement_details(
        statement=statement,
        page_count=page_count,
    )

    reconciliation_status = (
        "WARN"
        if reconciliation_is_warning and not reconciliation.reconciled
        else "PASS"
    )

    print(  # noqa: T201
        "         "
        f"reconciliation={reconciliation_status} "
        f"difference={reconciliation.difference}",
    )

    if show_transactions:
        _print_transactions(statement)


def _print_failure(  # noqa: PLR0913
    label: str,
    path: Path,
    *,
    statement: ParsedStatement,
    reconciliation: StatementReconciliation,
    page_count: int,
    show_transactions: bool,
) -> None:
    """Print a reconciliation failure for an otherwise parsed statement."""
    print(f"{label} FAIL {path}")  # noqa: T201

    _print_statement_details(
        statement=statement,
        page_count=page_count,
    )

    print(  # noqa: T201
        f"         reconciliation=FAIL difference={reconciliation.difference}",
    )

    if show_transactions:
        _print_transactions(statement)


def main() -> None:
    """Run archive smoke validation."""
    parser = build_parser()
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")

    try:
        statements = discover_statements(
            args.source,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.limit is not None:
        statements = statements[: args.limit]

    if not statements:
        parser.error(f"no PDF statements found under: {args.source}")

    failures = run_archive_smoke(
        statements,
        continue_on_error=args.continue_on_error,
        show_traceback=args.traceback,
        show_transactions=args.show_transactions,
        allow_reconciliation_failures=args.allow_reconciliation_failures,
    )

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
