"""
scripts/archive_smoke.py

Run private banking statement PDFs through the supported processing pipeline.
"""

from __future__ import annotations

import argparse
import traceback
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from banking_statements.domain import StatementSource
from banking_statements.processors import ProcessorRegistry
from banking_statements.processors.chase import (
    CHASE_SIGNATURES,
    ChaseCreditCardProcessor,
)
from banking_statements.processors.detection import InstitutionDetector
from banking_statements.text import PdfStatementTextReader

if TYPE_CHECKING:
    from collections.abc import Sequence


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


def build_institution_detector() -> InstitutionDetector:
    """Return detector configured with implemented institutions."""
    return InstitutionDetector((*CHASE_SIGNATURES,))


def build_processor_registry() -> ProcessorRegistry:
    """Return registry containing implemented statement processors."""
    return ProcessorRegistry(
        [
            ChaseCreditCardProcessor(),
        ]
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
) -> int:
    """Inspect statements and return the number of failures."""
    reader = PdfStatementTextReader()
    detector = build_institution_detector()
    registry = build_processor_registry()

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
            institution = detector.detect(text)
            processor = registry.select(text)
        except Exception as exc:  # noqa: BLE001
            failures += 1

            print(f"{label} FAIL {path.name}")  # noqa: T201
            print(  # noqa: T201
                f"         {type(exc).__name__}: {exc}",
            )

            if show_traceback:
                traceback.print_exc()

            if not continue_on_error:
                break

            continue

        _print_success(
            label,
            path,
            institution=institution,
            processor=processor.name,
            page_count=len(text.pages),
        )

    return failures


def _print_success(
    label: str,
    path: Path,
    *,
    institution: str,
    processor: str,
    page_count: int,
) -> None:
    """Print a concise statement-processing summary."""
    print(f"{label} PASS {path.name}")  # noqa: T201
    print(  # noqa: T201
        "         "
        f"institution={institution} "
        f"processor={processor} "
        f"pages={page_count}",
    )


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
    )

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
