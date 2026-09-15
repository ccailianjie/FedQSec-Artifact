"""Run the selected public workflow with lightweight demonstration branches."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fedqsec.accumulator import DynamicAccumulator
from fedqsec.crypto_core import GeneralizedSigncryptionCore, ProtectedOutput
from fedqsec.framework import ContextState, FedQSecController
from fedqsec.modes import CryptoMode, SecurityAction


class DemoAuthentication:
    def generate(self, message: bytes, parameter_profile: str) -> bytes:
        return b"auth:" + hashlib.sha256(parameter_profile.encode() + message).digest()


class DemoConfidentiality:
    def encapsulate(self, message: bytes, parameter_profile: str) -> bytes:
        return b"kem:" + hashlib.sha256(message + parameter_profile.encode()).digest()


class DemoDecision:
    def select(self, state: ContextState) -> SecurityAction:
        mode = CryptoMode.SIGNCRYPTION if state.priority == 3 else CryptoMode.SIGNATURE
        return SecurityAction(parameter_profile="lightweight", mode=mode)


class MemoryAudit:
    def __init__(self) -> None:
        self.records: list[ProtectedOutput] = []

    def append(self, output: ProtectedOutput) -> None:
        self.records.append(output)


def main() -> None:
    accumulator = DynamicAccumulator()
    crypto = GeneralizedSigncryptionCore(
        DemoAuthentication(), DemoConfidentiality(), accumulator
    )
    audit = MemoryAudit()
    controller = FedQSecController(DemoDecision(), crypto, audit)
    context = ContextState(speed=2, priority=3, density=2, credit=3)
    output = controller.process(b"example safety message", context, accumulator.initial_state)
    print(f"mode={output.mode.value}, counter={output.accumulator.counter}")
    print(f"audit_records={len(audit.records)}")


if __name__ == "__main__":
    main()

