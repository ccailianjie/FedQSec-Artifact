"""Small in-memory PBFT audit boundary for the public example."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from crypto.crypto_core import ProtectedOutput


@dataclass(frozen=True)
class CommitReceipt:
    record_digest: str
    quorum: int
    votes: int
    committed: bool


class AuditLedger:
    def __init__(self, replicas: int = 4) -> None:
        if replicas < 4:
            raise ValueError("The example requires at least four replicas")
        self.replicas = replicas
        self.records: list[CommitReceipt] = []

    def append(self, output: ProtectedOutput) -> None:
        self.commit(output)

    def commit(self, output: ProtectedOutput) -> CommitReceipt:
        digest = hashlib.sha256(
            output.body + output.accumulator.digest.encode("ascii")
        ).hexdigest()
        quorum = 2 * ((self.replicas - 1) // 3) + 1
        votes = self.replicas  # all healthy replicas in this miniature
        receipt = CommitReceipt(digest, quorum, votes, votes >= quorum)
        if receipt.committed:
            self.records.append(receipt)
        return receipt
