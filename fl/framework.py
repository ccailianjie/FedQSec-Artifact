"""Cloud-fog-edge workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from crypto.accumulator import AccumulatorState
from crypto.crypto_core import GeneralizedSigncryptionCore, ProtectedOutput
from crypto.modes import SecurityAction
from datapreprocessor.data_utils import ContextState


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
