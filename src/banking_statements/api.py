"""
src/banking_statements/api.py

High-level statement parsing API.
"""

from __future__ import annotations

from dataclasses import dataclass
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
    from banking_statements.domain import ParsedStatement
    from banking_statements.reconciliation import StatementReconciliation


@dataclass(frozen=True, slots=True)
class StatementParseResult:
    """Result of parsing and reconciling one banking statement."""

    statement: ParsedStatement
    reconciliation: StatementReconciliation
    page_count: int
    additional_accounts: tuple[StatementParseResult, ...] = ()

    @property
    def accounts(self) -> tuple[StatementParseResult, ...]:
        """Return every account result from this document in source order."""
        return (self, *self.additional_accounts)


def parse_statement(
    path: str | Path,
) -> StatementParseResult:
    """Parse and reconcile one supported banking statement PDF."""
    statement_path = Path(path)
    source = StatementSource(
        path=statement_path,
        sha256=_file_sha256(statement_path),
    )

    text = PdfStatementTextReader().read(source)

    detector = build_default_institution_detector()
    detector.detect(text)

    registry = build_default_processor_registry()
    processor = registry.select(text)

    statement = processor.parse(
        source,
        text,
    )
    reconciliation = reconcile_statement(statement)

    return StatementParseResult(
        statement=statement,
        reconciliation=reconciliation,
        page_count=len(text.pages),
        additional_accounts=tuple(
            StatementParseResult(
                statement=additional,
                reconciliation=reconcile_statement(additional),
                page_count=len(text.pages),
            )
            for additional in statement.additional_statements
        ),
    )


def parse_statements(
    source: str | Path,
) -> tuple[StatementParseResult, ...]:
    """Parse PDFs in path order, returning one result per reported account."""
    return tuple(
        account
        for path in _discover_statement_paths(Path(source))
        for account in parse_statement(path).accounts
    )


def _discover_statement_paths(
    source: Path,
) -> tuple[Path, ...]:
    """Return statement PDF paths in deterministic order."""
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


def _file_sha256(path: Path) -> str:
    """Return the SHA-256 digest for a statement file."""
    digest = sha256()

    with path.open("rb") as source_file:
        while chunk := source_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()
