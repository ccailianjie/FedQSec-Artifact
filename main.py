"""Run one connected FedQSec round with small in-memory messages."""

from __future__ import annotations

from datapreprocessor.data_utils import VehicleMessage
from fl.workflow import FedQSecWorkflow
from global_args import parse_args


def main() -> None:
    messages = [
        VehicleMessage("obu-1", 88, 3, 36, 94, b"emergency-braking"),
        VehicleMessage("obu-2", 52, 2, 22, 90, b"lane-change"),
        VehicleMessage("obu-3", 34, 1, 8, 18, b"inconsistent-position"),
        VehicleMessage("obu-4", 82, 3, 34, 92, b"collision-warning"),
        VehicleMessage("obu-5", 48, 2, 24, 86, b"traffic-density"),
        VehicleMessage("obu-6", 22, 1, 7, 84, b"periodic-status"),
    ]
    workflow = FedQSecWorkflow()
    workflow.attach([message.vehicle_id for message in messages])
    result = workflow.run_round(messages, target_id=parse_args().target)

    print("FedQSec example: 1 cloud, 2 RSUs, 6 OBUs, 4 audit replicas")
    for region in result.regional_updates:
        print(f"{region.rsu_id}: accepted={region.accepted}, rejected={region.rejected}")
    print(f"Global Q-table version: {result.global_version}")
    print(f"Selected action: {result.action.mode.value}/{result.action.parameter_profile}")
    print(f"Accumulator counter: {result.accumulator_counter}")
    print(f"PBFT receipt: committed={result.receipt.committed} "
          f"({result.receipt.votes}/{result.receipt.quorum})")
    assert result.receipt.committed and result.accumulator_counter == 1
    print("Workflow completed successfully.")


if __name__ == "__main__":
    main()
