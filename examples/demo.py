"""Runnable data-flow miniature of the FedQSec architecture.

The code follows the research implementation's main path:

Vehicle data -> state encoding -> local Q update -> RSU trust filtering and
regional aggregation -> cloud aggregation and model distribution -> adaptive
mode/parameter selection -> protected V2X packet -> accumulator audit record
-> PBFT commit.

The dataset reader, long training schedule, private lattice arithmetic, and
OMNeT++ event model are replaced by small deterministic adapters so that the
whole framework can run with the Python standard library.
"""

from __future__ import annotations

import hashlib
import csv
from dataclasses import dataclass, field
from pathlib import Path


N_STATES = 81
N_ACTIONS = 9
ALPHA = 0.1
GAMMA = 0.9
CREDIT_THRESHOLD = 60.0
MODES = ("sign", "encrypt", "signcrypt")
PARAMETER_SETS = ("I", "II", "III")


def new_q_table() -> list[list[float]]:
    return [[0.0 for _ in range(N_ACTIONS)] for _ in range(N_STATES)]


def copy_q_table(table: list[list[float]]) -> list[list[float]]:
    return [row[:] for row in table]


@dataclass(frozen=True)
class VehicleMessage:
    vehicle_id: str
    speed_kmh: float
    priority: int
    density: float
    behavior_score: float
    payload: bytes


@dataclass(frozen=True)
class ContextState:
    speed: int
    priority: int
    density: int
    credit: int
    index: int


@dataclass
class ModelUpdate:
    vehicle_id: str
    credit: float
    q_table: list[list[float]]


@dataclass(frozen=True)
class SecurityAction:
    action_id: int
    mode: str
    parameter_set: str


@dataclass(frozen=True)
class ProtectedPacket:
    vehicle_id: str
    action: SecurityAction
    body: bytes
    authentication_tag: str | None
    accumulator_previous: str
    accumulator_current: str
    accumulator_counter: int


@dataclass(frozen=True)
class CommitReceipt:
    record_hash: str
    prepare_votes: int
    commit_votes: int
    quorum: int
    committed: bool


@dataclass
class FlowTrace:
    events: list[str] = field(default_factory=list)

    def send(self, source: str, target: str, item: str) -> None:
        self.events.append(f"{source} -> {target}: {item}")

    def show(self) -> None:
        print("\nData flow")
        for number, event in enumerate(self.events, start=1):
            print(f"  {number:02d}. {event}")


class StateEncoder:
    """Quantize raw V2X fields exactly into the 3x3x3x3 state layout."""

    @staticmethod
    def _level(value: float, first: float, second: float) -> int:
        if value < first:
            return 1
        if value < second:
            return 2
        return 3

    def encode(self, message: VehicleMessage, credit_score: float) -> ContextState:
        speed = self._level(message.speed_kmh, 30, 60)
        priority = min(max(message.priority, 1), 3)
        density = self._level(message.density, 10, 30)
        credit = self._level(credit_score, 60, 90)
        index = (speed - 1) * 27 + (priority - 1) * 9 + (density - 1) * 3 + credit - 1
        return ContextState(speed, priority, density, credit, index)


def decode_action(action_id: int) -> SecurityAction:
    if not 0 <= action_id < N_ACTIONS:
        raise ValueError("action_id must be in [0, 8]")
    return SecurityAction(
        action_id=action_id,
        mode=MODES[action_id // 3],
        parameter_set=PARAMETER_SETS[action_id % 3],
    )


def reward_for(state: ContextState, action_id: int) -> float:
    """Reduced version of the full V2XSecurityEnv reward."""
    mode_id, parameter_id = divmod(action_id, 3)
    score = (
        {1: 10, 2: 20, 3: 35}[state.speed] * 0.3
        + {1: 10, 2: 20, 3: 35}[state.priority] * 0.4
        + {1: 10, 2: 20, 3: 30}[state.density] * 0.2
        + {1: 30, 2: 15, 3: 5}[state.credit] * 0.1
    )
    if state.priority == 3 or score >= 30:
        required_parameter = 2
        weights = (0.6, -0.2, -0.1, 0.1, 0.05)
    elif score >= 20:
        required_parameter = 1
        weights = (0.4, -0.2, -0.3, 0.1, 0.05)
    else:
        required_parameter = 0
        weights = (0.2, -0.2, -0.5, 0.1, 0.05)

    security_w, latency_w, resource_w, verify_w, success_w = weights
    parameter_ok = float(parameter_id >= required_parameter)
    latency_cost = mode_id * 0.3 + parameter_id * 0.2
    resource_cost = parameter_id * 0.15
    verifiability = (0.4, 0.6, 1.0)[mode_id]
    reward = (
        security_w * (0.5 + 0.5 * parameter_ok)
        + latency_w * latency_cost
        + resource_w * resource_cost
        + verify_w * verifiability
        + success_w * parameter_ok
    ) * 100.0
    if parameter_id < required_parameter:
        reward -= 10.0
    return reward


class TrustManager:
    """Connect message-level trust to model-update admission."""

    def __init__(self) -> None:
        self.credits: dict[str, float] = {}

    def observe(self, message: VehicleMessage) -> float:
        previous = self.credits.get(message.vehicle_id, 80.0)
        current = 0.3 * previous + 0.7 * message.behavior_score
        self.credits[message.vehicle_id] = min(100.0, max(0.0, current))
        return self.credits[message.vehicle_id]

    def accepts(self, vehicle_id: str) -> bool:
        return self.credits.get(vehicle_id, 0.0) >= CREDIT_THRESHOLD


class LocalQAgent:
    """Small tabular agent retaining the full code's update equation."""

    def __init__(self) -> None:
        self.q = new_q_table()

    def load_global(self, global_q: list[list[float]]) -> None:
        self.q = copy_q_table(global_q)

    def learn(self, state: int, action: int, reward: float, next_state: int) -> None:
        best_next = max(self.q[next_state])
        target = reward + GAMMA * best_next
        self.q[state][action] += ALPHA * (target - self.q[state][action])

    def reduced_training_round(self, state: ContextState, poisoned: bool = False) -> None:
        # Three compact sweeps stand in for the complete local iteration schedule.
        for _ in range(3):
            for action in range(N_ACTIONS):
                reward = reward_for(state, action)
                self.learn(state.index, action, -reward if poisoned else reward, state.index)


class VehicleOBU:
    """Vehicle endpoint: encode observations, train locally, and protect messages."""

    def __init__(self, vehicle_id: str, encoder: StateEncoder) -> None:
        self.vehicle_id = vehicle_id
        self.encoder = encoder
        self.agent = LocalQAgent()

    def create_update(
        self,
        message: VehicleMessage,
        credit: float,
        global_q: list[list[float]],
        poisoned: bool = False,
    ) -> tuple[ContextState, ModelUpdate]:
        self.agent.load_global(global_q)
        state = self.encoder.encode(message, credit)
        self.agent.reduced_training_round(state, poisoned)
        return state, ModelUpdate(self.vehicle_id, credit, copy_q_table(self.agent.q))

    def receive_global_model(self, global_q: list[list[float]]) -> None:
        self.agent.load_global(global_q)


class RSUNode:
    """Fog/RSU node: receive BSMs, filter updates, and form a regional model."""

    def __init__(self, rsu_id: str, trust: TrustManager, trace: FlowTrace) -> None:
        self.rsu_id = rsu_id
        self.trust = trust
        self.trace = trace
        self.vehicles: dict[str, VehicleOBU] = {}
        self.messages: dict[str, VehicleMessage] = {}
        self.states: dict[str, ContextState] = {}
        self.updates: list[ModelUpdate] = []

    def attach(self, vehicle: VehicleOBU) -> None:
        self.vehicles[vehicle.vehicle_id] = vehicle

    def receive_message(self, message: VehicleMessage, global_q: list[list[float]]) -> None:
        vehicle = self.vehicles[message.vehicle_id]
        self.trace.send(message.vehicle_id, self.rsu_id, "BSM + context observation")
        credit = self.trust.observe(message)
        state, update = vehicle.create_update(
            message,
            credit,
            global_q,
            poisoned=message.behavior_score < 30,
        )
        self.messages[message.vehicle_id] = message
        self.states[message.vehicle_id] = state
        self.updates.append(update)
        self.trace.send(message.vehicle_id, self.rsu_id, "local Q-table update")

    def aggregate(self, global_q: list[list[float]]) -> tuple[list[list[float]], list[str]]:
        eligible = [u for u in self.updates if self.trust.accepts(u.vehicle_id)]
        rejected = [u.vehicle_id for u in self.updates if not self.trust.accepts(u.vehicle_id)]
        if not eligible:
            return copy_q_table(global_q), rejected

        # Every OBU executes the same reduced number of local updates here, so
        # the paper's credit-and-sample weighting reduces to credit weighting.
        weights = [update.credit for update in eligible]
        denominator = sum(weights)
        regional_q = new_q_table()
        for state in range(N_STATES):
            for action in range(N_ACTIONS):
                delta = sum(
                    weight * (update.q_table[state][action] - global_q[state][action])
                    for update, weight in zip(eligible, weights)
                ) / denominator
                regional_q[state][action] = global_q[state][action] + delta

        self.trace.send(
            self.rsu_id,
            "cloud",
            f"regional Q-table ({len(eligible)} accepted, {len(rejected)} rejected)",
        )
        return regional_q, rejected

    def distribute(self, global_q: list[list[float]]) -> None:
        for vehicle in self.vehicles.values():
            vehicle.receive_global_model(global_q)
        self.trace.send("cloud", self.rsu_id, "global Q-table")


class CloudCoordinator:
    """Cloud node: combine regional models and return adaptive actions."""

    def __init__(self, trace: FlowTrace) -> None:
        self.trace = trace
        self.global_q = new_q_table()
        self.version = 0

    def aggregate(self, regional_tables: list[list[list[float]]]) -> list[list[float]]:
        self.global_q = [
            [
                sum(table[state][action] for table in regional_tables)
                / len(regional_tables)
                for action in range(N_ACTIONS)
            ]
            for state in range(N_STATES)
        ]
        self.version += 1
        self.trace.send("cloud", "RSUs/OBUs", f"global Q-table v{self.version}")
        return self.global_q

    def decide(self, state: ContextState) -> SecurityAction:
        action_id = max(range(N_ACTIONS), key=lambda a: self.global_q[state.index][a])
        action = decode_action(action_id)
        self.trace.send("cloud", "target OBU", f"action F={action.mode}/{action.parameter_set}")
        return action


class ReducedNTRUGSCInterface:
    """Executable mode boundary; private NTRU polynomial routines stay hidden."""

    def __init__(self, trace: FlowTrace) -> None:
        self.trace = trace
        self.accumulator = "ACC0"
        self.counter = 0

    @staticmethod
    def _hash(*parts: bytes) -> bytes:
        return hashlib.sha256(b"|".join(parts)).digest()

    def protect(self, message: VehicleMessage, action: SecurityAction) -> ProtectedPacket:
        authentication = self._hash(b"AUTH", action.parameter_set.encode(), message.payload)
        confidentiality = self._hash(b"CONF", message.payload, action.parameter_set.encode())
        if action.mode == "sign":
            body = message.payload
            tag = authentication.hex()
        elif action.mode == "encrypt":
            body = confidentiality
            tag = None
        else:
            body = confidentiality
            tag = authentication.hex()

        previous = self.accumulator
        self.counter += 1
        self.accumulator = self._hash(
            previous.encode(), action.mode.encode(), message.payload, str(self.counter).encode()
        ).hex()
        self.trace.send(message.vehicle_id, "RSU", f"protected packet ({action.mode})")
        return ProtectedPacket(
            vehicle_id=message.vehicle_id,
            action=action,
            body=body,
            authentication_tag=tag,
            accumulator_previous=previous,
            accumulator_current=self.accumulator,
            accumulator_counter=self.counter,
        )


class BlockchainGateway:
    """PBFT submission boundary corresponding to the OMNeT++ model."""

    def __init__(self, trace: FlowTrace, replicas: int = 4) -> None:
        self.trace = trace
        self.replicas = replicas
        self.ledger: list[dict[str, object]] = []

    def submit(self, packet: ProtectedPacket) -> CommitReceipt:
        record = {
            "vehicle_id": packet.vehicle_id,
            "mode": packet.action.mode,
            "parameter_set": packet.action.parameter_set,
            "payload_digest": hashlib.sha256(packet.body).hexdigest(),
            "accumulator": packet.accumulator_current,
            "counter": packet.accumulator_counter,
        }
        record_hash = hashlib.sha256(repr(sorted(record.items())).encode()).hexdigest()
        fault_bound = (self.replicas - 1) // 3
        quorum = 2 * fault_bound + 1
        prepare_votes = self.replicas
        commit_votes = self.replicas
        committed = prepare_votes >= quorum and commit_votes >= quorum
        if committed:
            self.ledger.append(record)
        self.trace.send("RSU", "PBFT replicas", "audit record")
        self.trace.send("PBFT replicas", "cloud", f"commit receipt ({commit_votes}/{quorum})")
        return CommitReceipt(record_hash, prepare_votes, commit_votes, quorum, committed)


class FedQSecFramework:
    """Connect every reduced component into one explicit data-flow pipeline."""

    def __init__(self) -> None:
        self.trace = FlowTrace()
        self.encoder = StateEncoder()
        self.trust = TrustManager()
        self.cloud = CloudCoordinator(self.trace)
        self.crypto = ReducedNTRUGSCInterface(self.trace)
        self.blockchain = BlockchainGateway(self.trace, replicas=4)
        self.rsus = [RSUNode("rsu-1", self.trust, self.trace), RSUNode("rsu-2", self.trust, self.trace)]

    def attach_vehicles(self, vehicle_ids: list[str]) -> None:
        for index, vehicle_id in enumerate(vehicle_ids):
            self.rsus[index % len(self.rsus)].attach(VehicleOBU(vehicle_id, self.encoder))

    def run_round(self, messages: list[VehicleMessage], target_vehicle: str) -> tuple[SecurityAction, CommitReceipt]:
        # 1) Vehicle observations and local updates flow upward to their RSUs.
        rsu_by_vehicle = {
            vehicle_id: rsu
            for rsu in self.rsus
            for vehicle_id in rsu.vehicles
        }
        for message in messages:
            rsu_by_vehicle[message.vehicle_id].receive_message(message, self.cloud.global_q)

        # 2) RSUs filter by credit and send regional models to the cloud.
        regional_tables = [rsu.aggregate(self.cloud.global_q)[0] for rsu in self.rsus]

        # 3) The cloud aggregates and distributes the global table.
        global_q = self.cloud.aggregate(regional_tables)
        for rsu in self.rsus:
            rsu.distribute(global_q)

        # 4) The cloud returns an action for the target message.
        target_rsu = rsu_by_vehicle[target_vehicle]
        target_message = target_rsu.messages[target_vehicle]
        target_state = target_rsu.states[target_vehicle]
        action = self.cloud.decide(target_state)

        # 5) The OBU generates a protected packet; RSU submits its audit record.
        packet = self.crypto.protect(target_message, action)
        receipt = self.blockchain.submit(packet)
        return action, receipt


def build_demo_messages() -> list[VehicleMessage]:
    path = Path(__file__).resolve().parents[1] / "data" / "sample_vehicle_messages.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return [
        VehicleMessage(
            row["vehicle_id"],
            float(row["speed_kmh"]),
            int(row["priority"]),
            float(row["vehicles_per_km"]),
            float(row["credit"]),
            row["payload"].encode("utf-8"),
        )
        for row in rows
    ]


def main() -> None:
    framework = FedQSecFramework()
    messages = build_demo_messages()
    framework.attach_vehicles([message.vehicle_id for message in messages])
    action, receipt = framework.run_round(messages, target_vehicle="obu-1")

    assert framework.cloud.version == 1
    assert framework.crypto.counter == 1
    assert receipt.committed
    assert len(framework.blockchain.ledger) == 1

    print("FedQSec reduced architecture")
    print("Topology: 1 cloud -> 2 RSUs -> 6 vehicle OBUs -> 4 PBFT replicas")
    print(f"State/action space: {N_STATES} x {N_ACTIONS}")
    print(f"Selected action: {action.action_id} ({action.mode}-{action.parameter_set})")
    print(f"Global model version: {framework.cloud.version}")
    print(f"Accumulator counter: {framework.crypto.counter}")
    print(f"PBFT committed: {receipt.committed} ({receipt.commit_votes}/{receipt.quorum})")
    framework.trace.show()
    print("\nWorkflow completed successfully.")


if __name__ == "__main__":
    main()
