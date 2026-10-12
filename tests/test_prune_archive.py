"""Tests for conservative archive selection and reversible application."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from scripts.prune_archive import (
    Record,
    apply_plan,
    digest_file,
    inspect_pdf,
    plan_archive,
    safe_path,
    select_records,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_selection_preserves_rare_features_failures_and_combinations() -> None:
    records = [
        Record("a.pdf", "a", ("common", "rare")),
        Record("b.pdf", "b", ("common",)),
        Record("c.pdf", "c", ("combination",)),
        Record("failed.pdf", "d", (), "failed"),
    ]
    keep, candidates = select_records(records)
    assert keep == ["a.pdf", "c.pdf", "failed.pdf"]
    assert candidates == ["b.pdf"]
    assert select_records(list(reversed(records))) == (keep, candidates)


def test_empty_profiles_are_kept() -> None:
    assert select_records([Record("empty.pdf", "x", ())]) == (
        ["empty.pdf"],
        [],
    )


def test_inspection_failure_is_retained(tmp_path: Path) -> None:
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"invalid")
    with (
        patch("scripts.prune_archive.coverage.Coverage"),
        patch(
            "scripts.prune_archive.parse_statement",
            side_effect=ValueError("unsupported"),
        ),
    ):
        record = inspect_pdf(path, tmp_path)
    assert record.error == "ValueError: unsupported"
    assert select_records([record]) == (["bad.pdf"], [])


def make_plan(tmp_path: Path) -> tuple[Path, Path, list[Record]]:
    """Build a synthetic private corpus with one redundant document."""
    root = tmp_path / "archive"
    root.mkdir()
    records = []
    for name in ("a.pdf", "b.pdf"):
        path = root / name
        path.write_bytes(name.encode())
        records.append(Record(name, digest_file(path), ("common",)))
    report = tmp_path / "plan.json"
    with patch("scripts.prune_archive.inspect_pdf", side_effect=records):
        plan_archive(root, report)
    return root, report, records


def test_preview_does_not_move_files(tmp_path: Path) -> None:
    root, report, _ = make_plan(tmp_path)
    assert len(list(root.glob("*.pdf"))) == 2
    plan = json.loads(report.read_text())
    assert plan["covered_by"] == {"b.pdf": ["a.pdf"]}


def test_apply_moves_only_redundant_files(tmp_path: Path) -> None:
    root, report, records = make_plan(tmp_path)
    destination = tmp_path / "removed"
    with patch("scripts.prune_archive.inspect_pdf", return_value=records[0]):
        apply_plan(report, destination)
    assert (root / "a.pdf").exists()
    assert not (root / "b.pdf").exists()
    assert (destination / "b.pdf").read_bytes() == b"b.pdf"
    assert (destination / "retention-manifest.json").exists()


@pytest.mark.parametrize(
    "change", ["bytes", "inventory", "parser", "selection", "validation"]
)
def test_stale_or_invalid_plan_moves_nothing(
    tmp_path: Path, change: str
) -> None:
    root, report, records = make_plan(tmp_path)
    plan = json.loads(report.read_text())
    if change == "bytes":
        (root / "a.pdf").write_bytes(b"changed")
    elif change == "inventory":
        (root / "new.pdf").write_bytes(b"new")
    elif change == "parser":
        plan["source_fingerprint"] = "stale"
    elif change == "selection":
        plan["keep"] = []
    report.write_text(json.dumps(plan))
    checked = (
        records[0]
        if change != "validation"
        else Record("a.pdf", "x", (), "failed")
    )
    destination = tmp_path / "removed"
    with (
        patch("scripts.prune_archive.inspect_pdf", return_value=checked),
        pytest.raises(ValueError, match=r"changed|modified"),
    ):
        apply_plan(report, destination)
    assert (root / "b.pdf").exists()
    assert not destination.exists()


@pytest.mark.parametrize("relative", ["../escape.pdf", "/escape.pdf"])
def test_manifest_paths_cannot_escape(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        safe_path(tmp_path, relative)


def test_apply_rejects_destination_inside_archive(tmp_path: Path) -> None:
    root, report, _ = make_plan(tmp_path)
    with pytest.raises(ValueError, match="outside"):
        apply_plan(report, root / "removed")


def test_move_failure_rolls_back(tmp_path: Path) -> None:
    root, report, records = make_plan(tmp_path)
    with (
        patch("scripts.prune_archive.inspect_pdf", return_value=records[0]),
        patch(
            "scripts.prune_archive.shutil.copyfile",
            side_effect=OSError("failed"),
        ),
        pytest.raises(OSError, match="failed"),
    ):
        apply_plan(report, tmp_path / "removed")
    assert (root / "a.pdf").exists()
    assert (root / "b.pdf").exists()


def test_pinned_document_is_kept() -> None:
    records = [
        Record("a.pdf", "a", ("common",)),
        Record("b.pdf", "b", ("common",), pinned=True),
    ]
    assert select_records(records) == (["b.pdf"], ["a.pdf"])
