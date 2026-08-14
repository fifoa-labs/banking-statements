"""
tests/domain/test_evidence.py

Tests for statement source evidence models.
"""

from __future__ import annotations

from pathlib import Path

from banking_statements.domain import SourceEvidence, StatementSource


def test_source_evidence_preserves_provenance() -> None:
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    evidence = SourceEvidence(
        source=source,
        page=2,
        section="Activity",
        raw_text="Sample transaction",
        processor="sample.monthly",
        sequence=4,
    )

    assert evidence.source is source
    assert evidence.page == 2
    assert evidence.section == "Activity"
    assert evidence.raw_text == "Sample transaction"
    assert evidence.processor == "sample.monthly"
    assert evidence.sequence == 4


def test_source_evidence_defaults_are_empty() -> None:
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    evidence = SourceEvidence(source=source)

    assert evidence.page is None
    assert evidence.section is None
    assert evidence.raw_text is None
    assert evidence.processor is None
    assert evidence.sequence is None
