from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FanCommand:
    """Normalized virtual fan commands in the inclusive range [0, 1]."""

    primary: float
    redundant: float


@dataclass(frozen=True)
class TelemetrySample:
    """One deterministic observation of the simulated ventilation plant."""

    step: int
    primary_command: float
    redundant_command: float
    primary_output: float
    redundant_output: float
    primary_tracking_residual: float
    airflow_zone_a: float
    airflow_zone_b: float
    co2_proxy_zone_a: float
    co2_proxy_zone_b: float
    temperature_c: float
    telemetry_valid: bool = True

    @property
    def total_airflow(self) -> float:
        return self.airflow_zone_a + self.airflow_zone_b
