from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class PropagationSnapshot:
    timestamp: str
    fault_active: bool
    airflow_act1: float
    airflow_duct2: float
    airflow_room3: float


class FaultPropagationGraph:
    def __init__(
        self,
        actuator_to_duct_weight: float = 1.0,
        duct_to_room_weight: float = 1.0,
        fault_drop_factor: float = 0.8,
    ) -> None:
        self.actuator_to_duct_weight = actuator_to_duct_weight
        self.duct_to_room_weight = duct_to_room_weight
        self.fault_drop_factor = fault_drop_factor

    def simulate(self, fault_active: bool, base_airflow: float = 1.0) -> Dict[str, float]:
        airflow_act1 = base_airflow * (self.fault_drop_factor if fault_active else 1.0)
        airflow_duct2 = airflow_act1 * self.actuator_to_duct_weight
        airflow_room3 = airflow_duct2 * self.duct_to_room_weight
        return {
            "airflow_act1": round(airflow_act1, 4),
            "airflow_duct2": round(airflow_duct2, 4),
            "airflow_room3": round(airflow_room3, 4),
        }

    def export_json(self, fault_active: bool) -> str:
        data = {
            "nodes": [
                {"id": "act1", "kind": "actuator"},
                {"id": "duct2", "kind": "duct"},
                {"id": "room3", "kind": "room"},
            ],
            "edges": [
                {"source": "act1", "target": "duct2", "weight": self.actuator_to_duct_weight},
                {"source": "duct2", "target": "room3", "weight": self.duct_to_room_weight},
            ],
            "state": self.simulate(fault_active=fault_active),
        }
        return json.dumps(data, indent=2)


def snapshots_to_rows(snapshots: Iterable[PropagationSnapshot]) -> list[dict[str, object]]:
    return [snapshot.__dict__ for snapshot in snapshots]
