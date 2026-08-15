"""
tests/processors/test_detection.py

Tests for institution detection.
"""

from __future__ import annotations

import pytest

from banking_statements.exceptions import (
    AmbiguousInstitutionError,
    UnsupportedInstitutionError,
)
from banking_statements.processors.detection import (
    InstitutionDetector,
    InstitutionSignature,
)
from banking_statements.text import StatementPage, StatementText


def make_statement_text(text: str) -> StatementText:
    """Build single-page statement text for detector tests."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=text,
            ),
        )
    )


def test_detector_exposes_signatures() -> None:
    signatures = (
        InstitutionSignature(
            institution="sample",
            required_markers=("ONE",),
        ),
    )
    detector = InstitutionDetector(signatures)

    assert detector.signatures == signatures


def test_detector_returns_unique_match() -> None:
    detector = InstitutionDetector(
        (
            InstitutionSignature(
                institution="alpha",
                required_markers=("ALPHA", "ACCOUNT"),
            ),
            InstitutionSignature(
                institution="beta",
                required_markers=("BETA",),
            ),
        )
    )

    result = detector.detect(
        make_statement_text("ALPHA ACCOUNT"),
    )

    assert result == "alpha"


def test_detector_rejects_no_match() -> None:
    detector = InstitutionDetector(
        (
            InstitutionSignature(
                institution="alpha",
                required_markers=("ALPHA",),
            ),
        )
    )

    with pytest.raises(
        UnsupportedInstitutionError,
        match="No known institution matched",
    ):
        detector.detect(
            make_statement_text("UNKNOWN"),
        )


def test_detector_rejects_multiple_matches() -> None:
    detector = InstitutionDetector(
        (
            InstitutionSignature(
                institution="alpha",
                required_markers=("ACCOUNT",),
            ),
            InstitutionSignature(
                institution="beta",
                required_markers=("ACCOUNT",),
            ),
        )
    )

    with pytest.raises(
        AmbiguousInstitutionError,
        match="alpha, beta",
    ):
        detector.detect(
            make_statement_text("ACCOUNT"),
        )
