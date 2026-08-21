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
from banking_statements.processors.capital_one import (
    CAPITAL_ONE_SIGNATURES,
    CapitalOneBusinessCreditCardProcessor,
    CapitalOneCheckingProcessor,
    CapitalOneCreditCardProcessor,
)
from banking_statements.processors.chase import (
    CHASE_SIGNATURES,
    ChaseBusinessCreditCardProcessor,
    ChaseCheckingProcessor,
    ChaseCreditCardProcessor,
    ChaseHelocProcessor,
)
from banking_statements.processors.discover import (
    DISCOVER_SIGNATURES,
    DiscoverCheckingProcessor,
    DiscoverCreditCardProcessor,
)
from banking_statements.processors.penfed import (
    PENFED_SIGNATURES,
    PenFedHelocProcessor,
)
from banking_statements.processors.us_bank import (
    US_BANK_SIGNATURES,
    USBankBusinessCheckingProcessor,
    USBankCreditCardProcessor,
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
        *CAPITAL_ONE_SIGNATURES,
        *PENFED_SIGNATURES,
        *US_BANK_SIGNATURES,
    )


def test_build_default_processor_registry() -> None:
    registry = build_default_processor_registry()

    assert len(registry.processors) == 21
    assert isinstance(registry.processors[0], ChaseCreditCardProcessor)
    assert isinstance(
        registry.processors[1],
        ChaseBusinessCreditCardProcessor,
    )
    assert isinstance(registry.processors[2], ChaseCheckingProcessor)
    assert isinstance(registry.processors[3], ChaseHelocProcessor)
    assert isinstance(registry.processors[4], WellsFargoCheckingProcessor)
    assert isinstance(registry.processors[5], WellsFargoCreditCardProcessor)
    assert isinstance(
        registry.processors[6],
        WellsFargoBusinessCheckingProcessor,
    )
    assert isinstance(
        registry.processors[7],
        WellsFargoBusinessCreditCardProcessor,
    )
    assert isinstance(
        registry.processors[8],
        WellsFargoBusinessLineOfCreditProcessor,
    )
    assert isinstance(
        registry.processors[9],
        AmericanExpressCreditCardProcessor,
    )
    assert isinstance(
        registry.processors[10],
        AmericanExpressBusinessCheckingProcessor,
    )
    assert isinstance(
        registry.processors[11],
        AmericanExpressBusinessLineOfCreditProcessor,
    )
    assert isinstance(
        registry.processors[12],
        AmericanExpressPersonalLoanProcessor,
    )
    assert isinstance(registry.processors[13], DiscoverCheckingProcessor)
    assert isinstance(registry.processors[14], DiscoverCreditCardProcessor)
    assert isinstance(registry.processors[15], CapitalOneCreditCardProcessor)
    assert isinstance(
        registry.processors[16],
        CapitalOneBusinessCreditCardProcessor,
    )
    assert isinstance(registry.processors[17], CapitalOneCheckingProcessor)
    assert isinstance(registry.processors[18], PenFedHelocProcessor)
    assert isinstance(
        registry.processors[19],
        USBankBusinessCheckingProcessor,
    )
    assert isinstance(registry.processors[20], USBankCreditCardProcessor)
