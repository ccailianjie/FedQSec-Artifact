"""Cloud-fog-edge workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .accumulator import AccumulatorState
from .crypto_core import GeneralizedSigncryptionCore, ProtectedOutput
from .modes import SecurityAction


@dataclass(frozen=True)
class ContextState:
    speed: int
    priority: int
    density: int
    credit: int


class DecisionEngine(Protocol):
    def select(self, state: ContextState) -> SecurityAction: ...


class AuditSink(Protocol):
    def append(self, output: ProtectedOutput) -> None: ...


class FedQSecController:
    def __init__(self, decision: DecisionEngine, crypto: GeneralizedSigncryptionCore, audit: AuditSink):
        self.decision = decision
        self.crypto = crypto
        self.audit = audit

    def process(
        self,
        message: bytes,
        context: ContextState,
        previous: AccumulatorState,
    ) -> ProtectedOutput:
        action = self.decision.select(context)
        output = self.crypto.generate(message, action, previous)
        self.audit.append(output)
        return output

