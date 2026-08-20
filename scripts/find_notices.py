"""
scripts/find_notices.py

Find, open, or delete private statement PDFs containing notice text.
"""

from __future__ import annotations

import argparse
import subprocess
from hashlib import sha256
from pathlib import Path

from banking_statements.domain import StatementSource
from banking_statements.text import PdfStatementTextReader

DEFAULT_PHRASE = "We are writing to"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Find private statement PDFs containing notice text.",
    )
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        default=Path("private-data/statements"),
        help="PDF file or directory to scan.",
    )
    parser.add_argument(
        "--phrase",
        default=DEFAULT_PHRASE,
        help=f'Text to search for. Default: "{DEFAULT_PHRASE}"',
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_matches",
        help="Open matching PDFs in Preview.",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete matching PDFs.",
    )
    return parser


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest for a file."""
    digest = sha256()

    with path.open("rb") as source_file:
        while chunk := source_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def discover_pdfs(source: Path) -> tuple[Path, ...]:
    """Return PDFs beneath a source in deterministic path order."""
    if source.is_file():
        return (source,)

    if not source.is_dir():
        msg = f"source does not exist: {source}"
        raise ValueError(msg)

    return tuple(
        sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.casefold() == ".pdf"
        )
    )


def find_matches(
    paths: tuple[Path, ...],
    *,
    phrase: str,
) -> tuple[Path, ...]:
    """Return PDFs whose extracted text contains the requested phrase."""
    reader = PdfStatementTextReader()
    needle = phrase.casefold()
    matches: list[Path] = []

    for path in paths:
        source = StatementSource(
            path=path,
            sha256=file_sha256(path),
        )
        text = reader.read(source)

        if needle in text.text.casefold():
            matches.append(path)

    return tuple(matches)


def main() -> None:
    """Find and optionally open or delete matching PDFs."""
    parser = build_parser()
    args = parser.parse_args()

    if args.open_matches and args.delete:
        parser.error("--open and --delete cannot be used together")

    try:
        paths = discover_pdfs(args.source)
    except ValueError as exc:
        parser.error(str(exc))

    matches = find_matches(
        paths,
        phrase=args.phrase,
    )

    for path in matches:
        print(path)  # noqa: T201

    print()  # noqa: T201
    print(f"Found {len(matches)} matching PDF(s).")  # noqa: T201

    if args.open_matches and matches:
        subprocess.run(  # noqa: S603
            ["open", "-a", "Preview", *(str(path) for path in matches)],  # noqa: S607
            check=True,
        )

    if args.delete:
        for path in matches:
            path.unlink()

        print(f"Deleted {len(matches)} matching PDF(s).")  # noqa: T201


if __name__ == "__main__":
    main()
