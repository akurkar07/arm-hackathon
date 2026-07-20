from icarus.agent import FanHealthMonitor, RollingZScoreDetector
from icarus.simulation import FanCommand, TwoZoneVentilationPlant


def test_health_monitor_requires_persistent_degradation() -> None:
    plant = TwoZoneVentilationPlant()
    monitor = FanHealthMonitor(persistence=3)
    sample = plant.observe(
        step=20,
        command=FanCommand(primary=0.75, redundant=0.0),
        primary_efficiency=0.45,
    )

    assert monitor.update(sample).state == "suspect"
    assert monitor.update(sample).state == "suspect"
    assessment = monitor.update(sample)

    assert assessment.state == "degraded"
    assert assessment.low_airflow is True


def test_invalid_telemetry_is_not_classified_as_a_fault() -> None:
    sample = TwoZoneVentilationPlant().observe(
        step=0,
        command=FanCommand(primary=0.75, redundant=0.0),
        telemetry_valid=False,
    )

    assert FanHealthMonitor().update(sample).state == "invalid"


def test_rolling_detector_flags_a_spike_after_warmup() -> None:
    detector = RollingZScoreDetector(window=10, threshold=3.0, warmup=5)
    detector.prime([0.01, 0.02, 0.01, 0.02, 0.01])

    z_score = detector.update(0.5)

    assert detector.is_anomaly(z_score)
