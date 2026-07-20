from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from .models import TelemetrySample


FAULT_TYPES = ("stuck", "high_torque", "power_drop")


@dataclass
class FaultState:
    name: Optional[str] = None
    stuck_position: Optional[float] = None

    @property
    def active(self) -> bool:
        return self.name is not None


class FaultSimulator:
    def __init__(self, fault_probability: float = 0.10, rng: Optional[random.Random] = None) -> None:
        self.fault_probability = fault_probability
        self.rng = rng or random.Random()
        self.state = FaultState()

    def maybe_start_fault(self, enabled: bool, current_position: float) -> FaultState:
        if enabled and not self.state.active and self.rng.random() < self.fault_probability:
            name = self.rng.choice(FAULT_TYPES)
            stuck_position = current_position if name == "stuck" else None
            self.state = FaultState(name=name, stuck_position=stuck_position)
        elif not enabled:
            self.state = FaultState()
        return self.state

    def clear(self) -> None:
        self.state = FaultState()

    def apply(self, sample: TelemetrySample, fault_enabled: bool) -> tuple[TelemetrySample, FaultState]:
        self.maybe_start_fault(fault_enabled, sample.pos_norm)

        pos_norm = sample.pos_norm
        torque_norm = sample.torque_norm
        power = sample.power

        if self.state.name == "stuck" and self.state.stuck_position is not None:
            pos_norm = self.state.stuck_position
        elif self.state.name == "high_torque":
            torque_norm = min(1.0, torque_norm * 2.0)
        elif self.state.name == "power_drop":
            power = 0.0

        return (
            TelemetrySample(
                pos_norm=pos_norm,
                torque_norm=torque_norm,
                power=power,
                temp=sample.temp,
                setpoint=sample.setpoint,
            ),
            self.state,
        )
