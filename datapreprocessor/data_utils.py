"""Compact context encoding for the public architecture example."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContextState:
    speed: int
    priority: int
    density: int
    credit: int


@dataclass(frozen=True)
class VehicleMessage:
    vehicle_id: str
    speed_kmh: float
    priority: int
    vehicles_per_km: float
    credit: float
    payload: bytes


def _level(value: float, first: float, second: float) -> int:
    if value < first:
        return 1
    if value < second:
        return 2
    return 3


def encode_context(message: VehicleMessage) -> ContextState:
    """Map four three-level observations to one of 81 context states."""
    return ContextState(
        speed=_level(message.speed_kmh, 30, 60),
        priority=min(3, max(1, message.priority)),
        density=_level(message.vehicles_per_km, 10, 30),
        credit=_level(message.credit, 60, 90),
    )


def state_index(state: ContextState) -> int:
    return ((state.speed - 1) * 27 + (state.priority - 1) * 9
            + (state.density - 1) * 3 + state.credit - 1)


def load_vehicle_messages(path: str | Path) -> list[VehicleMessage]:
    """Read the small vehicle-context CSV used by the executable example."""
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return [
        VehicleMessage(
            vehicle_id=row["vehicle_id"],
            speed_kmh=float(row["speed_kmh"]),
            priority=int(row["priority"]),
            vehicles_per_km=float(row["vehicles_per_km"]),
            credit=float(row["credit"]),
            payload=row["payload"].encode("utf-8"),
        )
        for row in rows
    ]
