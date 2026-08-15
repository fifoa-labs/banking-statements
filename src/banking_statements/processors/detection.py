"""
src/banking_statements/processors/detection.py

Institution detection for banking statement text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from banking_statements.exceptions import (
    AmbiguousInstitutionError,
    UnsupportedInstitutionError,
)

if TYPE_CHECKING:
    from banking_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class InstitutionSignature:
    """Text markers identifying a statement-producing institution."""

    institution: str
    required_markers: tuple[str, ...]


class InstitutionDetector:
    """Detect the institution responsible for a statement."""

    def __init__(
        self,
        signatures: tuple[InstitutionSignature, ...],
    ) -> None:
        self._signatures = signatures

    @property
    def signatures(self) -> tuple[InstitutionSignature, ...]:
        """Return configured institution signatures."""
        return self._signatures

    def detect(self, text: StatementText) -> str:
        """Return the uniquely matching institution."""
        matches = tuple(
            signature
            for signature in self._signatures
            if all(
                marker in text.text for marker in signature.required_markers
            )
        )

        if not matches:
            msg = "No known institution matched this statement."
            raise UnsupportedInstitutionError(msg)

        institutions = tuple(
            dict.fromkeys(signature.institution for signature in matches)
        )

        if len(institutions) > 1:
            names = ", ".join(institutions)
            msg = f"Multiple institutions matched this statement: {names}."
            raise AmbiguousInstitutionError(msg)

        return institutions[0]
