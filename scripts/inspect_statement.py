"""
scripts/inspect_statement.py

Inspect page-aware text extracted from a private banking statement PDF.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path

from banking_statements.domain import StatementSource
from banking_statements.text import PdfStatementTextReader


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect page-aware text extracted from a banking statement PDF."
        ),
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to the banking statement PDF.",
    )
    parser.add_argument(
        "--page",
        type=int,
        help="Show only one one-based PDF page.",
    )
    parser.add_argument(
        "--head",
        type=int,
        help="Limit displayed text to the first N characters per page.",
    )
    return parser


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest for a file."""
    digest = sha256()

    with path.open("rb") as source_file:
        while chunk := source_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def inspect_statement(
    path: Path,
    *,
    page_number: int | None = None,
    head: int | None = None,
) -> None:
    """Extract and display normalized statement page text."""
    source = StatementSource(
        path=path,
        sha256=file_sha256(path),
    )
    statement_text = PdfStatementTextReader().read(source)

    print(f"Source: {source.path}")  # noqa: T201
    print(f"SHA-256: {source.sha256}")  # noqa: T201
    print(f"Pages: {len(statement_text.pages)}")  # noqa: T201

    for page in statement_text.pages:
        if page_number is not None and page.number != page_number:
            continue

        text = page.text

        if head is not None:
            text = text[:head]

        print()  # noqa: T201
        print("=" * 80)  # noqa: T201
        print(f"PAGE {page.number}")  # noqa: T201
        print("=" * 80)  # noqa: T201
        print(text)  # noqa: T201


def main() -> None:
    """Run statement text inspection."""
    parser = build_parser()
    args = parser.parse_args()

    path: Path = args.source

    if not path.is_file():
        parser.error(f"statement does not exist: {path}")

    if args.page is not None and args.page < 1:
        parser.error("--page must be at least 1")

    if args.head is not None and args.head < 1:
        parser.error("--head must be at least 1")

    inspect_statement(
        path,
        page_number=args.page,
        head=args.head,
    )


if __name__ == "__main__":
    main()
