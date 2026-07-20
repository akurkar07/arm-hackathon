from __future__ import annotations

from datetime import datetime, timezone

from .faults import FaultSimulator
from .health import ActuatorHealthMonitor, ZScoreDetector
from .impact import FaultPropagationGraph
from .models import RuntimeSample, TelemetrySample


def process_telemetry(
    telemetry: TelemetrySample,
    health: ActuatorHealthMonitor,
    detector: ZScoreDetector,
    impact: FaultPropagationGraph,
    faults: FaultSimulator | None = None,
    fault_enabled: bool = False,
    timestamp: datetime | None = None,
    test_number: int = 1,
    source_mode: str = "belimo-influx",
) -> tuple[RuntimeSample, str | None]:
    timestamp = timestamp or datetime.now(timezone.utc)

    fault_state = None
    if faults is not None:
        telemetry, fault_state = faults.apply(telemetry, fault_enabled=fault_enabled)

    fault_active = bool(fault_state.active) if fault_state is not None else False
    fault_code = fault_state.name if fault_state is not None and fault_state.name else "none"
    airflow = impact.simulate(fault_active=fault_active)
    metrics = health.update(
        timestamp=timestamp,
        setpoint=telemetry.setpoint,
        pos_norm=telemetry.pos_norm,
        torque_norm=telemetry.torque_norm,
        power=telemetry.power,
    )
    alert = detector.update(telemetry.pos_norm, telemetry.torque_norm)

    sample = RuntimeSample(
        timestamp=timestamp,
        pos_norm=telemetry.pos_norm,
        torque_norm=telemetry.torque_norm,
        power=telemetry.power,
        temp=telemetry.temp,
        setpoint=telemetry.setpoint,
        delta_t_proxy=telemetry.setpoint - telemetry.temp,
        fault_active=float(fault_active),
        fault_code=fault_code,
        airflow_act1=airflow["airflow_act1"],
        airflow_duct2=airflow["airflow_duct2"],
        airflow_room3=airflow["airflow_room3"],
        settling_error=metrics.settling_error,
        moving=metrics.moving,
        stroke_seconds=metrics.stroke_seconds,
        health_score=metrics.health_score,
        health_state=metrics.health_state,
        test_number=test_number,
        source_mode=source_mode,
    )
    return sample, alert
