from __future__ import annotations

import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from .models import RuntimeSample, TelemetrySample
from .utils import clamp, parse_influx_frames

EPOCH_TS = datetime.fromtimestamp(0, tz=timezone.utc)


class BelimoInfluxBridge:
    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str = "actuator-data",
        verify_ssl: bool = False,
        torque_scale: float = 1000.0,
        temp_scale: float = 100.0,
    ) -> None:
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.verify_ssl = verify_ssl
        self.torque_scale = torque_scale
        self.temp_scale = temp_scale
        self.client: Optional[InfluxDBClient] = None
        self.query_api = None
        self.write_api = None

    def connect(self, timeout_seconds: int = 30) -> None:
        if not self.token:
            raise RuntimeError("Belimo Influx token is required")

        self.client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org,
            verify_ssl=self.verify_ssl,
        )
        self._wait_until_ready(timeout_seconds)
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def _wait_until_ready(self, timeout_seconds: int) -> None:
        if self.client is None:
            return
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                if self.client.ping():
                    return
            except Exception:
                pass
            time.sleep(1.0)
        raise RuntimeError(f"InfluxDB at {self.url} did not become ready within {timeout_seconds}s")

    def close(self) -> None:
        if self.client is not None:
            self.client.close()

    def write_process(self, setpoint_norm: float, test_number: int) -> None:
        if self.write_api is None:
            raise RuntimeError("Belimo bridge is not connected")

        df = pd.DataFrame(
            [
                {
                    "timestamp": EPOCH_TS,
                    "setpoint_position_%": float(clamp(setpoint_norm, 0.0, 1.0) * 100.0),
                    "test_number": int(test_number),
                }
            ]
        ).set_index("timestamp")
        self.write_api.write(
            bucket=self.bucket,
            org=self.org,
            record=df,
            write_precision=WritePrecision.MS,
            data_frame_measurement_name="_process",
            data_frame_tag_columns=[],
        )

    def read_measurement(self) -> TelemetrySample:
        if self.query_api is None:
            raise RuntimeError("Belimo bridge is not connected")

        query = f"""
from(bucket: "{self.bucket}")
  |> range(start: 0)
  |> filter(fn: (r) => r["_measurement"] == "measurements")
  |> group(columns: ["_field"])
  |> last()
  |> drop(columns: ["_start", "_stop"])
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
"""
        frame = parse_influx_frames(self.query_api.query_data_frame(query))
        if frame.empty:
            raise RuntimeError("No telemetry found in measurement 'measurements'")

        row = frame.iloc[-1].to_dict()
        pos_pct = float(row.get("feedback_position_%", row.get("setpoint_position_%", 0.0)) or 0.0)
        torque_nmm = float(row.get("motor_torque_Nmm", 0.0) or 0.0)
        power_w = float(row.get("power_W", 0.0) or 0.0)
        temp_c = float(row.get("internal_temperature_deg_C", 0.0) or 0.0)
        setpoint_pct = float(row.get("setpoint_position_%", pos_pct) or pos_pct)

        return TelemetrySample(
            pos_norm=clamp(pos_pct / 100.0, 0.0, 1.0),
            torque_norm=clamp(torque_nmm / self.torque_scale, 0.0, 1.0),
            power=power_w,
            temp=clamp(temp_c / self.temp_scale, 0.0, 1.0),
            setpoint=clamp(setpoint_pct / 100.0, 0.0, 1.0),
        )


class InfluxAnalyticsSink:
    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        bucket: str,
        measurement: str = "belimo_actuator",
        actuator_id: str = "1",
        verify_ssl: bool = True,
    ) -> None:
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.measurement = measurement
        self.actuator_id = actuator_id
        self.verify_ssl = verify_ssl
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None

    def connect(self, timeout_seconds: int = 30) -> None:
        if not self.token:
            raise RuntimeError("Influx token is required")
        self.client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org,
            verify_ssl=self.verify_ssl,
        )
        self._wait_until_ready(timeout_seconds)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def _wait_until_ready(self, timeout_seconds: int) -> None:
        if self.client is None:
            return
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                if self.client.ping():
                    return
            except Exception:
                pass
            time.sleep(1.0)
        raise RuntimeError(f"InfluxDB at {self.url} did not become ready within {timeout_seconds}s")

    def write(self, sample: RuntimeSample, alert: Optional[str] = None) -> None:
        if self.write_api is None:
            raise RuntimeError("Influx sink is not connected")

        point = (
            Point(self.measurement)
            .tag("actuator_id", self.actuator_id)
            .tag("fault_code", sample.fault_code)
            .tag("source_mode", sample.source_mode)
            .tag("test_number", str(sample.test_number))
            .field("anomaly", 1.0 if alert else 0.0)
            .time(sample.timestamp, WritePrecision.NS)
        )
        for key, value in asdict(sample).items():
            if key in {"timestamp", "fault_code", "source_mode", "test_number"}:
                continue
            point.field(key, value)

        self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
