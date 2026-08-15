"""
src/banking_statements/processors/defaults.py

Default institution detector and processor registry composition.
"""

from __future__ import annotations

from banking_statements.processors.chase import (
    CHASE_SIGNATURES,
    ChaseCheckingProcessor,
    ChaseCreditCardProcessor,
)
from banking_statements.processors.detection import InstitutionDetector
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
        )
    )


def build_default_processor_registry() -> ProcessorRegistry:
    """Return the registry containing all supported statement processors."""
    return ProcessorRegistry(
        (
            ChaseCreditCardProcessor(),
            ChaseCheckingProcessor(),
            WellsFargoCheckingProcessor(),
            WellsFargoCreditCardProcessor(),
            WellsFargoBusinessCheckingProcessor(),
            WellsFargoBusinessCreditCardProcessor(),
            WellsFargoBusinessLineOfCreditProcessor(),
        )
    )
