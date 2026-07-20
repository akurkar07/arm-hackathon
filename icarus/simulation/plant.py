from __future__ import annotations

from dataclasses import dataclass

from .models import FanCommand, TelemetrySample


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass
class TwoZoneVentilationPlant:
    """Small deterministic plant used to generate replayable telemetry.

    Airflow units are normalized. The model is intentionally compact: it makes
    command-to-output tracking and recovery observable without claiming physical
    fidelity to a real life-support system.
    """

    primary_capacity: float = 0.8
    redundant_capacity: float = 0.5
    zone_a_share: float = 0.55
    nominal_temperature_c: float = 22.0
    nominal_co2_proxy: float = 800.0
    target_airflow: float = 0.6

    def observe(
        self,
        step: int,
        command: FanCommand,
        primary_efficiency: float = 1.0,
        telemetry_valid: bool = True,
    ) -> TelemetrySample:
        primary_command = _clamp(command.primary, 0.0, 1.0)
        redundant_command = _clamp(command.redundant, 0.0, 1.0)
        efficiency = _clamp(primary_efficiency, 0.0, 1.0)

        primary_output = primary_command * efficiency
        redundant_output = redundant_command
        total_airflow = (
            primary_output * self.primary_capacity
            + redundant_output * self.redundant_capacity
        )
        airflow_zone_a = total_airflow * self.zone_a_share
        airflow_zone_b = total_airflow - airflow_zone_a
        airflow_deficit = max(self.target_airflow - total_airflow, 0.0)

        return TelemetrySample(
            step=step,
            primary_command=round(primary_command, 4),
            redundant_command=round(redundant_command, 4),
            primary_output=round(primary_output, 4),
            redundant_output=round(redundant_output, 4),
            primary_tracking_residual=round(primary_command - primary_output, 4),
            airflow_zone_a=round(airflow_zone_a, 4),
            airflow_zone_b=round(airflow_zone_b, 4),
            co2_proxy_zone_a=round(self.nominal_co2_proxy + airflow_deficit * 900.0, 2),
            co2_proxy_zone_b=round(self.nominal_co2_proxy + airflow_deficit * 750.0, 2),
            temperature_c=round(self.nominal_temperature_c + airflow_deficit * 3.0, 2),
            telemetry_valid=telemetry_valid,
        )
