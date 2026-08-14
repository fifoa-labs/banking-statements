"""
src/banking_statements/domain/evidence.py

Source identity and provenance models for parsed statement data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class StatementSource:
    """Identity of a source statement."""

    path: Path
    sha256: str


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    """Location of normalized data within a source statement."""

    source: StatementSource
    page: int | None = None
    section: str | None = None
    raw_text: str | None = None
    processor: str | None = None
    sequence: int | None = None
