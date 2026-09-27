"""Hash-chain state used for continuity and replay pre-screening."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class AccumulatorState:
    counter: int
    digest: str


class DynamicAccumulator:
    def __init__(self, initial_digest: str = "ACC0") -> None:
        self.initial_state = AccumulatorState(counter=0, digest=initial_digest)

    @staticmethod
    def _encode(previous: AccumulatorState, mode: str, payload: bytes) -> bytes:
        fields = (previous.digest, str(previous.counter + 1), mode)
        return "|".join(fields).encode("utf-8") + b"|" + payload

    def update(self, previous: AccumulatorState, mode: str, payload: bytes) -> AccumulatorState:
        digest = hashlib.sha256(self._encode(previous, mode, payload)).hexdigest()
        return AccumulatorState(counter=previous.counter + 1, digest=digest)

    def verify(
        self,
        previous: AccumulatorState,
        candidate: AccumulatorState,
        mode: str,
        payload: bytes,
    ) -> bool:
        return candidate == self.update(previous, mode, payload)

