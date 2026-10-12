"""Plan and reversibly reduce a private PDF regression corpus.

Profiles preserve observed branch arcs, recognized institution signatures,
input-format flags, and account/transaction shapes. They are empirical
regression coverage, not proof that two documents are interchangeable.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

import coverage

from banking_statements import parse_statement
from banking_statements.processors import build_default_institution_detector
from banking_statements.text import PdfStatementTextReader
from scripts.archive_smoke import discover_statements

if TYPE_CHECKING:
    from collections.abc import Sequence

    from banking_statements.api import StatementParseResult


@dataclass(frozen=True)
class Record:
    """One validated document and its observed regression features."""

    path: str
    digest: str
    features: tuple[str, ...]
    error: str = ""
    pinned: bool = False


def digest_file(path: Path) -> str:
    """Hash current file bytes independently of any saved plan."""
    return sha256(path.read_bytes()).hexdigest()


def result_features(result: StatementParseResult) -> set[str]:
    """Describe shapes for every account, preserving feature combinations."""
    features = {f"document:accounts={len(result.accounts)}"}
    for account in result.accounts:
        statement = account.statement
        prefix = statement.processor
        shapes = {
            f"type={statement.account.account_type.value}",
            (
                "year-boundary="
                f"{statement.period.start.year != statement.period.end.year}"
            ),
            (
                "month-boundary="
                f"{statement.period.start.month != statement.period.end.month}"
            ),
            f"activity={'empty' if not statement.transactions else 'present'}",
        }
        for label, amount in (
            ("opening", statement.balances.opening_balance),
            ("closing", statement.balances.closing_balance),
        ):
            sign = (
                "negative"
                if amount < 0
                else "zero"
                if amount == 0
                else "positive"
            )
            shapes.add(f"{label}={sign}")
        shapes.update(
            f"direction={transaction.direction.value}"
            for transaction in statement.transactions
        )
        features.update(f"{prefix}:{shape}" for shape in shapes)
        features.add(f"{prefix}:combination=" + ";".join(sorted(shapes)))
    return features


def inspect_pdf(path: Path, root: Path) -> Record:
    """Parse all accounts, collecting observed package branch arcs."""
    digest = digest_file(path)
    tracer = coverage.Coverage(
        branch=True,
        data_file=None,
        source=["banking_statements"],
    )
    tracer.set_option(
        "run:disable_warnings", ["module-not-measured", "no-data-collected"]
    )
    try:
        tracer.start()
        try:
            result = parse_statement(path)
        finally:
            tracer.stop()
        if not all(
            account.reconciliation.reconciled for account in result.accounts
        ):
            msg = "one or more accounts did not reconcile"
            raise ValueError(msg)  # noqa: TRY301
        features = result_features(result)
        text = PdfStatementTextReader().read(result.statement.source).text
        for index, signature in enumerate(
            build_default_institution_detector().signatures
        ):
            if all(marker in text for marker in signature.required_markers):
                features.add(f"signature:{signature.institution}:{index}")
        # Observed grammar variants from historical regressions.
        for marker in (
            "-$",
            "$(",
            "($",
            "transaction detail",
            "transactiondetail",
            "Continued on next page",
            "Transactions (Continued)",
            "Spark Cash card |",
            "Spark Cash credit card |",
        ):
            if marker in text:
                features.add(f"input:{marker}")
        if "through" in text:
            features.add(f"input:spaced-through={' through ' in text}")
        data = tracer.get_data()
        for filename in sorted(data.measured_files()):
            relative = filename.split("banking_statements/", 1)[-1]
            features.update(
                f"arc:{relative}:{start}:{end}"
                for start, end in data.arcs(filename) or ()
            )
        return Record(
            str(path.relative_to(root)), digest, tuple(sorted(features))
        )
    except Exception as exc:  # noqa: BLE001
        return Record(
            str(path.relative_to(root)),
            digest,
            (),
            f"{type(exc).__name__}: {exc}",
        )


def select_records(records: Sequence[Record]) -> tuple[list[str], list[str]]:
    """Preserve the feature union with deterministic greedy selection."""
    keep = [record.path for record in records if record.error or record.pinned]
    remaining = [
        record for record in records if not record.error and not record.pinned
    ]
    uncovered = set().union(*(set(record.features) for record in remaining))
    for record in records:
        if record.pinned:
            uncovered.difference_update(record.features)
    while uncovered:
        best = min(
            remaining,
            key=lambda record: (
                -len(set(record.features) & uncovered),
                record.path,
            ),
        )
        keep.append(best.path)
        uncovered.difference_update(best.features)
        remaining.remove(best)
    # Empty feature records should never disappear without another byte copy.
    for record in remaining[:]:
        if not record.features:
            keep.append(record.path)
            remaining.remove(record)
    return sorted(keep), sorted(record.path for record in remaining)


def source_fingerprint() -> str:
    """Bind plans to the exact parser and pruning implementation."""
    import banking_statements  # noqa: PLC0415

    root = Path(banking_statements.__file__).parent
    digest = sha256(Path(__file__).read_bytes())
    for path in sorted(root.rglob("*.py")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def plan_archive(
    root: Path,
    report: Path,
    keep_paths: Sequence[str] = (),
) -> dict[str, object]:
    """Validate every PDF and save a local reviewable manifest."""
    root = root.resolve()
    if report.suffix.lower() != ".json":
        msg = "report must be a JSON file"
        raise ValueError(msg)
    records = []
    paths = discover_statements(root)
    if not paths:
        msg = "no PDF statements found"
        raise ValueError(msg)
    available = {str(path.relative_to(root)) for path in paths}
    if not set(keep_paths) <= available:
        msg = "pinned paths must be PDF paths relative to the archive root"
        raise ValueError(msg)
    for index, path in enumerate(paths, 1):
        record = inspect_pdf(path, root)
        record = replace(record, pinned=record.path in keep_paths)
        records.append(record)
        status = "FAIL: keep" if record.error else "PASS"
        print(  # noqa: T201
            f"[{index}/{len(paths)}] {status} {record.path}"
        )
    keep, candidates = select_records(records)
    by_path = {record.path: record for record in records}
    replacements = {}
    for candidate in candidates:
        required = set(by_path[candidate].features)
        covering = []
        for retained in keep:
            covered = required & set(by_path[retained].features)
            if covered:
                covering.append(retained)
                required.difference_update(covered)
        replacements[candidate] = covering
    manifest: dict[str, object] = {
        "schema": 1,
        "root": str(root),
        "source_fingerprint": source_fingerprint(),
        "limitation": (
            "Observed branches and feature combinations only; "
            "unseen grammar may be lost. No semantic equivalence guarantee."
        ),
        "records": [asdict(record) for record in records],
        "keep": keep,
        "candidates": candidates,
        "covered_by": replacements,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(manifest, indent=2) + "\n")
    print(  # noqa: T201
        f"PDFs={len(records)} keep={len(keep)} "
        f"candidates={len(candidates)} "
        f"failures={sum(bool(record.error) for record in records)}"
    )
    print(f"Preview only. Manifest: {report}")  # noqa: T201
    return manifest


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal and symlink paths in a saved manifest."""
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        msg = "unsafe manifest path"
        raise ValueError(msg)
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        msg = "symlink paths are not supported"
        raise ValueError(msg)
    if not path.resolve().is_relative_to(root):
        msg = "manifest path escapes archive"
        raise ValueError(msg)
    return path


def apply_plan(report: Path, destination: Path) -> None:  # noqa: C901, PLR0912
    """Verify a plan and retained corpus before moving candidates."""
    manifest = json.loads(report.read_text())
    if (
        manifest["schema"] != 1
        or manifest["source_fingerprint"] != source_fingerprint()
    ):
        msg = "parser or plan version changed; create a fresh preview"
        raise ValueError(msg)
    root = Path(manifest["root"]).resolve()
    destination = destination.absolute()
    if (
        destination.exists()
        or destination.resolve().is_relative_to(root)
        or root.is_relative_to(destination.resolve())
    ):
        msg = "destination must be a new directory outside the archive"
        raise ValueError(msg)
    records = [
        Record(
            item["path"],
            item["digest"],
            tuple(item["features"]),
            item["error"],
            item["pinned"],
        )
        for item in manifest["records"]
    ]
    paths = {record.path for record in records}
    if paths != {
        str(path.relative_to(root)) for path in discover_statements(root)
    }:
        msg = "archive inventory changed; create a fresh preview"
        raise ValueError(msg)
    keep, candidates = select_records(records)
    if keep != manifest["keep"] or candidates != manifest["candidates"]:
        msg = "manifest selection was modified"
        raise ValueError(msg)
    for record in records:
        if digest_file(safe_path(root, record.path)) != record.digest:
            msg = f"file changed: {record.path}; create a fresh preview"
            raise ValueError(msg)
    expected = set().union(*(set(record.features) for record in records))
    observed: set[str] = set()
    for record in records:
        if record.path in keep and not record.error:
            checked = inspect_pdf(safe_path(root, record.path), root)
            if checked.error or checked.features != record.features:
                msg = f"retained validation changed: {record.path}"
                raise ValueError(msg)
            observed.update(checked.features)
    if observed != expected:
        msg = "retained corpus does not preserve observed coverage"
        raise ValueError(msg)
    destination.mkdir(parents=True)
    moved: list[str] = []
    try:
        for relative in candidates:
            target = safe_path(destination, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(safe_path(root, relative)), target)
            moved.append(relative)
        shutil.copyfile(report, destination / "retention-manifest.json")
    except Exception:
        for relative in reversed(moved):
            shutil.move(str(destination / relative), root / relative)
        raise
    print(  # noqa: T201
        f"Moved {len(moved)} PDFs to {destination}; "
        f"retained {len(keep)}. Nothing deleted."
    )


def main() -> None:
    """Preview by default; explicitly apply an acknowledged plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?")
    parser.add_argument(
        "--report", type=Path, default=Path("private-data/prune-manifest.json")
    )
    parser.add_argument("--keep", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--accept-observed-coverage", action="store_true")
    args = parser.parse_args()
    if args.apply:
        if args.destination is None or not args.accept_observed_coverage:
            parser.error(
                "--apply requires --destination and --accept-observed-coverage"
            )
        apply_plan(args.report, args.destination)
    else:
        if args.source is None or not args.source.is_dir():
            parser.error("preview requires an archive directory")
        plan_archive(args.source, args.report, args.keep)


if __name__ == "__main__":
    main()
