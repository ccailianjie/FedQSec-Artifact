"""Mode-gated NTRU-GSC workflow with private lattice routines abstracted."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .accumulator import AccumulatorState, DynamicAccumulator
from .modes import CryptoMode, SecurityAction


class AuthenticationBranch(Protocol):
    def generate(self, message: bytes, parameter_profile: str) -> bytes: ...


class ConfidentialityBranch(Protocol):
    def encapsulate(self, message: bytes, parameter_profile: str) -> bytes: ...


@dataclass(frozen=True)
class ProtectedOutput:
    mode: CryptoMode
    body: bytes
    accumulator: AccumulatorState


class GeneralizedSigncryptionCore:
    """Combine selected branches under one mode-controlled public workflow."""

    def __init__(
        self,
        authentication: AuthenticationBranch,
        confidentiality: ConfidentialityBranch,
        accumulator: DynamicAccumulator,
    ) -> None:
        self.authentication = authentication
        self.confidentiality = confidentiality
        self.accumulator = accumulator

    def generate(
        self,
        message: bytes,
        action: SecurityAction,
        previous: AccumulatorState,
    ) -> ProtectedOutput:
        components: list[bytes] = []
        if action.mode.uses_authentication:
            components.append(self.authentication.generate(message, action.parameter_profile))
        if action.mode.uses_confidentiality:
            components.append(self.confidentiality.encapsulate(message, action.parameter_profile))
        body = b"|".join(components)
        state = self.accumulator.update(previous, action.mode.value, body)
        return ProtectedOutput(action.mode, body, state)

