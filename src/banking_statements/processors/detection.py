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

        if len(matches) > 1:
            institutions = ", ".join(
                signature.institution for signature in matches
            )
            msg = (
                "Multiple institutions matched this statement: "
                f"{institutions}."
            )
            raise AmbiguousInstitutionError(msg)

        return matches[0].institution
