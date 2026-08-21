"""
src/banking_statements/processors/defaults.py

Default institution detector and processor registry composition.
"""

from __future__ import annotations

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
    ChaseCheckingProcessor,
    ChaseCreditCardProcessor,
    ChaseHelocProcessor,
)
from banking_statements.processors.detection import InstitutionDetector
from banking_statements.processors.discover import (
    DISCOVER_SIGNATURES,
    DiscoverCheckingProcessor,
    DiscoverCreditCardProcessor,
)
from banking_statements.processors.penfed import (
    PENFED_SIGNATURES,
    PenFedHelocProcessor,
)
from banking_statements.processors.registry import ProcessorRegistry
from banking_statements.processors.wellsfargo import (
    WELLS_FARGO_SIGNATURES,
    WellsFargoBusinessCheckingProcessor,
    WellsFargoBusinessCreditCardProcessor,
    WellsFargoBusinessLineOfCreditProcessor,
    WellsFargoCheckingProcessor,
    WellsFargoCreditCardProcessor,
)


def build_default_institution_detector() -> InstitutionDetector:
    """Return the detector configured for all supported institutions."""
    return InstitutionDetector(
        (
            *CHASE_SIGNATURES,
            *WELLS_FARGO_SIGNATURES,
            *AMERICAN_EXPRESS_SIGNATURES,
            *DISCOVER_SIGNATURES,
            *CAPITAL_ONE_SIGNATURES,
            *PENFED_SIGNATURES,
        )
    )


def build_default_processor_registry() -> ProcessorRegistry:
    """Return the registry containing all supported statement processors."""
    return ProcessorRegistry(
        (
            ChaseCreditCardProcessor(),
            ChaseCheckingProcessor(),
            ChaseHelocProcessor(),
            WellsFargoCheckingProcessor(),
            WellsFargoCreditCardProcessor(),
            WellsFargoBusinessCheckingProcessor(),
            WellsFargoBusinessCreditCardProcessor(),
            WellsFargoBusinessLineOfCreditProcessor(),
            AmericanExpressCreditCardProcessor(),
            AmericanExpressBusinessCheckingProcessor(),
            AmericanExpressBusinessLineOfCreditProcessor(),
            AmericanExpressPersonalLoanProcessor(),
            DiscoverCheckingProcessor(),
            DiscoverCreditCardProcessor(),
            CapitalOneCreditCardProcessor(),
            CapitalOneBusinessCreditCardProcessor(),
            CapitalOneCheckingProcessor(),
            PenFedHelocProcessor(),
        )
    )
