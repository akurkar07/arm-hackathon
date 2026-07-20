from __future__ import annotations

import math
from collections import deque
from datetime import datetime
from statistics import fmean, pstdev
from typing import Deque, Optional, Tuple

from .models import HealthMetrics
from .utils import clamp


class ActuatorHealthMonitor:
    def __init__(self, settle_band: float = 0.03, motion_band: float = 0.01) -> None:
        self.settle_band = settle_band
        self.motion_band = motion_band
        self.last_setpoint: Optional[float] = None
        self.command_started_at: Optional[datetime] = None
        self.stroke_seconds = 0.0

    def update(
        self,
        timestamp: datetime,
        setpoint: float,
        pos_norm: float,
        torque_norm: float,
        power: float,
    ) -> HealthMetrics:
        error = abs(setpoint - pos_norm)
        moving = error > self.motion_band or power > 0.1

        if self.last_setpoint is None or abs(setpoint - self.last_setpoint) > self.motion_band:
            self.command_started_at = timestamp
            self.last_setpoint = setpoint

        if self.command_started_at is not None:
            self.stroke_seconds = max((timestamp - self.command_started_at).total_seconds(), 0.0)

        if error <= self.settle_band:
            state = "tracking"
        elif self.stroke_seconds > 25 and moving:
            state = "slow_response"
        elif self.stroke_seconds > 25 and not moving:
            state = "stalled"
        elif torque_norm > 0.8:
            state = "high_load"
        else:
            state = "transition"

        health_score = 1.0
        health_score -= min(error * 1.5, 0.5)
        health_score -= min(self.stroke_seconds / 120.0, 0.3)
        if state == "stalled":
            health_score -= 0.3
        if state == "high_load":
            health_score -= 0.2

        return HealthMetrics(
            settling_error=round(error, 4),
            moving=float(moving),
            stroke_seconds=round(self.stroke_seconds, 2),
            health_score=round(clamp(health_score, 0.0, 1.0), 3),
            health_state=state,
        )


class ZScoreDetector:
    def __init__(self, window: int = 30, threshold: float = 3.0) -> None:
        self.threshold = threshold
        self.torque_deltas: Deque[float] = deque(maxlen=window)
        self.pos_deltas: Deque[float] = deque(maxlen=window)
        self.previous: Optional[Tuple[float, float]] = None

    @staticmethod
    def _z_score(values: Deque[float], current: float) -> float:
        if len(values) < 5:
            return 0.0
        std = pstdev(values)
        if math.isclose(std, 0.0):
            return 0.0
        return (current - fmean(values)) / std

    def update(self, pos_norm: float, torque_norm: float) -> Optional[str]:
        if self.previous is None:
            self.previous = (pos_norm, torque_norm)
            return None

        pos_delta = pos_norm - self.previous[0]
        torque_delta = torque_norm - self.previous[1]
        pos_z = self._z_score(self.pos_deltas, pos_delta)
        torque_z = self._z_score(self.torque_deltas, torque_delta)
        self.pos_deltas.append(pos_delta)
        self.torque_deltas.append(torque_delta)
        self.previous = (pos_norm, torque_norm)

        if abs(pos_z) > self.threshold or abs(torque_z) > self.threshold:
            return (
                f"ALERT z-score anomaly "
                f"pos_delta={pos_delta:.3f} z={pos_z:.2f} "
                f"torque_delta={torque_delta:.3f} z={torque_z:.2f}"
            )
        return None
