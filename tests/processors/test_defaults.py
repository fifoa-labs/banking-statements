"""
tests/processors/test_defaults.py

Tests for default institution detector and processor registry composition.
"""

from __future__ import annotations

from banking_statements.processors import (
    build_default_institution_detector,
    build_default_processor_registry,
)
from banking_statements.processors.chase import (
    CHASE_SIGNATURES,
    ChaseCheckingProcessor,
    ChaseCreditCardProcessor,
)
from banking_statements.processors.wellsfargo import (
    WELLS_FARGO_SIGNATURES,
    WellsFargoCheckingProcessor,
)


def test_build_default_institution_detector() -> None:
    detector = build_default_institution_detector()

    assert detector.signatures == (
        *CHASE_SIGNATURES,
        *WELLS_FARGO_SIGNATURES,
    )


def test_build_default_processor_registry() -> None:
    registry = build_default_processor_registry()

    assert len(registry.processors) == 3
    assert isinstance(registry.processors[0], ChaseCreditCardProcessor)
    assert isinstance(registry.processors[1], ChaseCheckingProcessor)
    assert isinstance(registry.processors[2], WellsFargoCheckingProcessor)
