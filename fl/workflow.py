"""Orchestrate one vehicle-to-cloud-to-ledger data-flow example."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from crypto.accumulator import DynamicAccumulator
from blockchain.audit import AuditLedger, CommitReceipt
from crypto.crypto_core import GeneralizedSigncryptionCore
from datapreprocessor.data_utils import VehicleMessage, encode_context
from .client import Vehicle
from .server import RSU, RegionalUpdate
from .coordinator import Cloud
from .framework import FedQSecController
from crypto.modes import SecurityAction


class ExampleAuthentication:
    def generate(self, message: bytes, parameter_profile: str) -> bytes:
        return hashlib.sha256(b"AUTH|" + parameter_profile.encode() + message).digest()


class ExampleConfidentiality:
    def encapsulate(self, message: bytes, parameter_profile: str) -> bytes:
        return hashlib.sha256(b"ENC|" + parameter_profile.encode() + message).digest()


@dataclass(frozen=True)
class RoundSummary:
    regional_updates: tuple[RegionalUpdate, ...]
    global_version: int
    action: SecurityAction
    accumulator_counter: int
    receipt: CommitReceipt


class FedQSecWorkflow:
    def __init__(self) -> None:
        self.cloud = Cloud()
        self.rsus = (RSU("rsu-1"), RSU("rsu-2"))
        self.audit = AuditLedger(replicas=4)
        self.accumulator = DynamicAccumulator()
        self.accumulator_state = self.accumulator.initial_state
        crypto = GeneralizedSigncryptionCore(
            ExampleAuthentication(), ExampleConfidentiality(), self.accumulator
        )
        self.controller = FedQSecController(self.cloud, crypto, self.audit)

    def attach(self, vehicle_ids: list[str]) -> None:
        for number, vehicle_id in enumerate(vehicle_ids):
            self.rsus[number % len(self.rsus)].attach(Vehicle(vehicle_id, number))

    def run_round(self, messages: list[VehicleMessage], target_id: str) -> RoundSummary:
        by_id = {message.vehicle_id: message for message in messages}
        if len(by_id) != len(messages) or target_id not in by_id:
            raise ValueError("Vehicle IDs must be unique and include the target")
        rsu_by_vehicle = {
            vehicle_id: rsu for rsu in self.rsus for vehicle_id in rsu.vehicles
        }
        for message in messages:
            rsu_by_vehicle[message.vehicle_id].receive(message, self.cloud.q)
        regions = tuple(rsu.aggregate(self.cloud.q) for rsu in self.rsus)
        global_q = self.cloud.aggregate(list(regions))
        for rsu in self.rsus:
            rsu.distribute(global_q)
        target = by_id[target_id]
        output = self.controller.process(
            target.payload, encode_context(target), self.accumulator_state
        )
        self.accumulator_state = output.accumulator
        return RoundSummary(
            regions, self.cloud.version, self.cloud.select(encode_context(target)),
            output.accumulator.counter, self.audit.records[-1],
        )
