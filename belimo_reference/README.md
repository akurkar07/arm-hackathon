# Belimo Extract

Reusable Belimo actuator telemetry code extracted from the START Hack project.
This folder intentionally strips the hackathon frontend, launch scripts, generated
run data, demo timing, local Docker setup, and hardcoded event defaults.

## What Is Here

- `bridge.py`: read Belimo InfluxDB `measurements`, write actuator commands to `_process`, and optionally write normalized analytics.
- `models.py`: small dataclasses for raw telemetry, health metrics, and enriched runtime samples.
- `health.py`: actuator health states and z-score anomaly detection.
- `faults.py`: optional demo fault injection for `stuck`, `high_torque`, and `power_drop`.
- `impact.py`: simple actuator-to-room airflow impact model.
- `pipeline.py`: one helper that combines telemetry, faults, health, anomaly, and impact into a `RuntimeSample`.

## Minimal Usage

```python
from belimo_extract.bridge import BelimoInfluxBridge
from belimo_extract.health import ActuatorHealthMonitor, ZScoreDetector
from belimo_extract.impact import FaultPropagationGraph
from belimo_extract.pipeline import process_telemetry

bridge = BelimoInfluxBridge(
    url="http://BELIMO-INFLUX:8086",
    token="...",
    org="belimo",
    bucket="actuator-data",
)
bridge.connect()

health = ActuatorHealthMonitor()
detector = ZScoreDetector()
impact = FaultPropagationGraph()

telemetry = bridge.read_measurement()
sample, alert = process_telemetry(telemetry, health, detector, impact)
```

## Belimo Fields Expected

The bridge expects the Belimo event-style measurement `measurements` with these
fields where available:

- `feedback_position_%`
- `setpoint_position_%`
- `motor_torque_Nmm`
- `power_W`
- `internal_temperature_deg_C`

Commands are written to `_process` with `setpoint_position_%` and `test_number`.

## Import Note

The top-level folder keeps the requested name, `belimo extract`. The actual
Python package inside it is `belimo_extract`, so the clean transplant target is:

```text
your_project/
  belimo_extract/
    bridge.py
    health.py
    ...
```
