import pytest

from icarus.scenarios import PrimaryFanDegradation
from icarus.simulation import FanCommand, TwoZoneVentilationPlant


def test_primary_degradation_reduces_airflow_and_creates_residual() -> None:
    plant = TwoZoneVentilationPlant()
    scenario = PrimaryFanDegradation(starts_at_step=5, degraded_efficiency=0.45)
    command = FanCommand(primary=0.75, redundant=0.0)

    nominal = plant.observe(4, command, scenario.primary_efficiency(4))
    degraded = plant.observe(5, command, scenario.primary_efficiency(5))

    assert nominal.total_airflow == pytest.approx(0.6)
    assert degraded.total_airflow < 0.3
    assert degraded.primary_tracking_residual == pytest.approx(0.4125)


def test_bounded_redundant_command_restores_airflow_above_floor() -> None:
    plant = TwoZoneVentilationPlant()
    command = FanCommand(primary=0.75, redundant=0.7)

    recovered = plant.observe(10, command, primary_efficiency=0.45)

    assert command.redundant <= 0.8
    assert recovered.total_airflow > 0.6


def test_commands_are_clamped_to_normalized_range() -> None:
    sample = TwoZoneVentilationPlant().observe(
        0,
        FanCommand(primary=2.0, redundant=-1.0),
    )

    assert sample.primary_command == 1.0
    assert sample.redundant_command == 0.0
