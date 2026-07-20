# ICARUS Belimo Reference Branch

This branch preserves the complete reusable Belimo actuator extraction from an
earlier START Hack project. It exists as reference material for ICARUS while the
team develops its simulated habitat ventilation system.

Nothing in `belimo_reference/` should be treated as the final ICARUS design or
as production control software. The code is retained so useful ideas can be
adapted deliberately without losing their original context.

## Where It Came From

The source was **Belimo Insight Copilot**, built for the Belimo challenge at
START Hack 2026. That prototype monitored actuator telemetry, calculated health
signals, injected demonstration faults, estimated downstream airflow impact,
and exchanged measurements and commands through InfluxDB.

The original hackathon project included a frontend, launch scripts, generated
run data, Grafana assets, Docker configuration, and demo-specific defaults. A
smaller reusable package was extracted from that project into the local
`belimo extract` folder. This branch contains that extraction in full and
unchanged under `belimo_reference/`.

The extraction's own README is preserved at
`belimo_reference/README.md`.

## Why It Is Here

ICARUS and the Belimo prototype share several useful concepts:

- normalized actuator and sensor telemetry;
- command-versus-output tracking residuals;
- health states based on movement, load, and settling behaviour;
- rolling anomaly detection;
- deterministic or injected fault conditions;
- propagation from actuator state to airflow impact;
- a pipeline that enriches each telemetry sample with health and fault data.

Keeping the full package on a separate branch gives the team a stable reference
without adding Belimo, InfluxDB, pandas, or demo assumptions to the main ICARUS
implementation.

## What Is Included

```text
belimo_reference/
|-- README.md
|-- requirements.txt
`-- belimo_extract/
    |-- __init__.py
    |-- bridge.py
    |-- faults.py
    |-- health.py
    |-- impact.py
    |-- models.py
    |-- pipeline.py
    `-- utils.py
```

The package provides:

- `BelimoInfluxBridge` for reading event telemetry and writing actuator
  setpoints;
- `InfluxAnalyticsSink` for storing enriched runtime samples;
- `ActuatorHealthMonitor` for tracking, load, stall, and response states;
- `ZScoreDetector` as a dependency-free rolling anomaly detector;
- `FaultSimulator` for stuck, high-torque, and power-drop demonstrations;
- `FaultPropagationGraph` for simple actuator-to-duct-to-room airflow impact;
- dataclasses for telemetry, health metrics, and enriched runtime samples;
- `process_telemetry` for composing those pieces into one processing step.

## Relationship To ICARUS

The code should be used as a source of patterns, tests, and domain ideas. Before
moving anything into the ICARUS implementation:

1. Rename Belimo actuator fields around ICARUS primary and redundant fans.
2. Replace random demo faults with deterministic scenario schedules.
3. Keep the z-score and rule-based health logic as baselines, not as substitutes
   for the planned ONNX model.
4. Keep live InfluxDB integration out of the first simulation slice.
5. Replace the single actuator-to-room impact model with the declared two-zone
   ventilation plant.
6. Preserve ICARUS safety requirements, including bounded virtual commands and
   `HAND_BACK` for invalid telemetry.

The active ICARUS implementation belongs on its own feature branches. This
branch is intentionally an archive and comparison point.

## Running The Reference Package

Install its optional integration dependencies with:

```bash
python -m pip install -r belimo_reference/requirements.txt
```

The Influx bridge requires a reachable InfluxDB instance and valid connection
settings. The health, fault, impact, and model modules can be imported without
connecting to live hardware, although importing the package root currently
loads the InfluxDB and pandas dependencies.

## Safety And Scope

- This is hackathon prototype code, not certified control software.
- It must not issue commands to real habitat, life-support, or production HVAC
  equipment.
- No claim about Arm performance, model accuracy, or physical-system safety is
  established by this reference branch.
