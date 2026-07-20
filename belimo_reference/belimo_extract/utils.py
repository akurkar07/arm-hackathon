from __future__ import annotations

from typing import Any

import pandas as pd


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def normalize_percent(value: float) -> float:
    if value > 1.0:
        return clamp(value / 100.0, 0.0, 1.0)
    return clamp(value, 0.0, 1.0)


def parse_influx_frames(frames: Any) -> pd.DataFrame:
    if isinstance(frames, list):
        valid = [frame for frame in frames if isinstance(frame, pd.DataFrame) and not frame.empty]
        if not valid:
            return pd.DataFrame()
        return pd.concat(valid, ignore_index=True)
    if isinstance(frames, pd.DataFrame):
        return frames
    return pd.DataFrame()
