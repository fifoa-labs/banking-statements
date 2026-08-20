"""
tests/processors/test_defaults.py

Tests for default institution detector and processor registry composition.
"""

from __future__ import annotations

from banking_statements.processors import (
    build_default_institution_detector,
    build_default_processor_registry,
)
from banking_statements.processors.american_express import (
    AMERICAN_EXPRESS_SIGNATURES,
    AmericanExpressBusinessCheckingProcessor,
    AmericanExpressBusinessLineOfCreditProcessor,
    AmericanExpressCreditCardProcessor,
    AmericanExpressPersonalLoanProcessor,
)
from banking_statements.processors.chase import (
    CHASE_SIGNATURES,
    ChaseCheckingProcessor,
    ChaseCreditCardProcessor,
    ChaseHelocProcessor,
)
from banking_statements.processors.discover import (
    DISCOVER_SIGNATURES,
    DiscoverCheckingProcessor,
    DiscoverCreditCardProcessor,
)
from banking_statements.processors.wellsfargo import (
    WELLS_FARGO_SIGNATURES,
    WellsFargoBusinessCheckingProcessor,
    WellsFargoBusinessCreditCardProcessor,
    WellsFargoBusinessLineOfCreditProcessor,
    WellsFargoCheckingProcessor,
    WellsFargoCreditCardProcessor,
)


def test_build_default_institution_detector() -> None:
    detector = build_default_institution_detector()

    assert detector.signatures == (
        *CHASE_SIGNATURES,
        *WELLS_FARGO_SIGNATURES,
        *AMERICAN_EXPRESS_SIGNATURES,
        *DISCOVER_SIGNATURES,
    )


def test_build_default_processor_registry() -> None:
    registry = build_default_processor_registry()

    assert len(registry.processors) == 14
    assert isinstance(registry.processors[0], ChaseCreditCardProcessor)
    assert isinstance(registry.processors[1], ChaseCheckingProcessor)
    assert isinstance(registry.processors[2], ChaseHelocProcessor)
    assert isinstance(registry.processors[3], WellsFargoCheckingProcessor)
    assert isinstance(registry.processors[4], WellsFargoCreditCardProcessor)
    assert isinstance(
        registry.processors[5],
        WellsFargoBusinessCheckingProcessor,
    )
    assert isinstance(
        registry.processors[6],
        WellsFargoBusinessCreditCardProcessor,
    )
    assert isinstance(
        registry.processors[7],
        WellsFargoBusinessLineOfCreditProcessor,
    )
    assert isinstance(
        registry.processors[8],
        AmericanExpressCreditCardProcessor,
    )
    assert isinstance(
        registry.processors[9],
        AmericanExpressBusinessCheckingProcessor,
    )
    assert isinstance(
        registry.processors[10],
        AmericanExpressBusinessLineOfCreditProcessor,
    )
    assert isinstance(
        registry.processors[11],
        AmericanExpressPersonalLoanProcessor,
    )
    assert isinstance(registry.processors[12], DiscoverCheckingProcessor)
    assert isinstance(registry.processors[13], DiscoverCreditCardProcessor)
