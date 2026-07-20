from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from statistics import fmean, pstdev
from typing import Deque, Iterable

from icarus.simulation.models import TelemetrySample


@dataclass(frozen=True)
class HealthAssessment:
    state: str
    score: float
    tracking_residual: float
    low_airflow: bool
    consecutive_degraded_samples: int


class FanHealthMonitor:
    """Rule-based baseline for validation and synthetic-data labelling.

    This is deliberately separate from the planned ONNX inference path. It
    supplies an interpretable baseline and does not stand in for the challenge
    model or its Arm benchmark evidence.
    """

    def __init__(
        self,
        residual_threshold: float = 0.15,
        airflow_floor: float = 0.5,
        persistence: int = 3,
    ) -> None:
        if persistence < 1:
            raise ValueError("persistence must be at least 1")
        self.residual_threshold = residual_threshold
        self.airflow_floor = airflow_floor
        self.persistence = persistence
        self._degraded_samples = 0

    def update(self, sample: TelemetrySample) -> HealthAssessment:
        if not sample.telemetry_valid:
            self._degraded_samples = 0
            return HealthAssessment("invalid", 0.0, 0.0, False, 0)

        residual = abs(sample.primary_tracking_residual)
        low_airflow = sample.total_airflow < self.airflow_floor
        suspicious = residual > self.residual_threshold and low_airflow
        self._degraded_samples = self._degraded_samples + 1 if suspicious else 0

        if self._degraded_samples >= self.persistence:
            state = "degraded"
        elif suspicious:
            state = "suspect"
        else:
            state = "nominal"

        score = 1.0 - min(residual, 0.6) - (0.2 if low_airflow else 0.0)
        return HealthAssessment(
            state=state,
            score=round(max(0.0, score), 3),
            tracking_residual=round(residual, 4),
            low_airflow=low_airflow,
            consecutive_degraded_samples=self._degraded_samples,
        )


class RollingZScoreDetector:
    """Small dependency-free anomaly baseline for a scalar telemetry signal."""

    def __init__(self, window: int = 30, threshold: float = 3.0, warmup: int = 5) -> None:
        if window < warmup:
            raise ValueError("window must be at least as large as warmup")
        self.threshold = threshold
        self.warmup = warmup
        self._values: Deque[float] = deque(maxlen=window)

    def update(self, value: float) -> float | None:
        z_score = self.score(value)
        self._values.append(value)
        return z_score

    def score(self, value: float) -> float | None:
        if len(self._values) < self.warmup:
            return None
        standard_deviation = pstdev(self._values)
        if math.isclose(standard_deviation, 0.0):
            return math.inf if not math.isclose(value, fmean(self._values)) else 0.0
        return (value - fmean(self._values)) / standard_deviation

    def is_anomaly(self, z_score: float | None) -> bool:
        return z_score is not None and abs(z_score) > self.threshold

    def prime(self, values: Iterable[float]) -> None:
        for value in values:
            self.update(value)
