from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TelemetrySample:
    pos_norm: float
    torque_norm: float
    power: float
    temp: float
    setpoint: float


@dataclass(frozen=True)
class HealthMetrics:
    settling_error: float
    moving: float
    stroke_seconds: float
    health_score: float
    health_state: str


@dataclass(frozen=True)
class RuntimeSample:
    timestamp: datetime
    pos_norm: float
    torque_norm: float
    power: float
    temp: float
    setpoint: float
    delta_t_proxy: float
    fault_active: float
    fault_code: str
    airflow_act1: float
    airflow_duct2: float
    airflow_room3: float
    settling_error: float
    moving: float
    stroke_seconds: float
    health_score: float
    health_state: str
    test_number: int
    source_mode: str
