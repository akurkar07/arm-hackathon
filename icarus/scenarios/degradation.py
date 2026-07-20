from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrimaryFanDegradation:
    """A repeatable loss of primary-fan output after a configured step."""

    starts_at_step: int = 20
    degraded_efficiency: float = 0.45

    def __post_init__(self) -> None:
        if self.starts_at_step < 0:
            raise ValueError("starts_at_step must be non-negative")
        if not 0.0 <= self.degraded_efficiency <= 1.0:
            raise ValueError("degraded_efficiency must be between 0 and 1")

    def is_active(self, step: int) -> bool:
        return step >= self.starts_at_step

    def primary_efficiency(self, step: int) -> float:
        return self.degraded_efficiency if self.is_active(step) else 1.0
