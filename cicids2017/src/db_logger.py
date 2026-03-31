"""
Database Logger — writes IDS predictions to InfluxDB.
Plugs into the replay engine as a callback.
"""

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


class IDSDBLogger:
    """
    Writes each prediction to InfluxDB for Grafana to visualize.
    Each prediction becomes a data point with:
      - timestamp
      - prediction (Benign/DoS/etc.)
      - confidence score
      - is_attack flag
      - flow metadata
    """

    def __init__(self):
        self.url = "http://localhost:8086"
        self.token = "rNYcxhvq8IOUOXSMZpJFdTbX61W2dPr7wgurvYmAji47gAy3nmEM4D-NGptINm49obeeESU71q7Ksdsqbgv6Ig=="
        self.org = "idsproject"
        self.bucket = "network_traffic"

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

        # Test connection
        health = self.client.health()
        print(f"[DB] Connected to InfluxDB: {health.status}")

    def log_prediction(self, flow_number, timestamp, flow_data, result, stats):
        """
        Callback function for the replay engine.
        Writes one prediction to InfluxDB.
        """
        point = (
            Point("ids_prediction")
            .tag("prediction", result['prediction'])
            .tag("is_attack", str(result['is_attack']))
            .field("confidence", result['confidence'])
            .field("flow_number", flow_number)
            .field("attack_count", stats['attacks'])
            .field("total_count", stats['total'])
            .field("attack_rate", stats['attacks'] / max(stats['total'], 1) * 100)
        )

        # Add flow metadata if available
        try:
            point = point.field("dst_port", int(flow_data.get('Destination Port', 0)))
            point = point.field("flow_duration", float(flow_data.get('Flow Duration', 0)))
            point = point.field("fwd_packets", int(flow_data.get('Total Fwd Packets', 0)))
            point = point.field("bwd_packets", int(flow_data.get('Total Backward Packets', 0)))
            point = point.field("flow_bytes_per_s", float(flow_data.get('Flow Bytes/s', 0)))
        except (ValueError, TypeError):
            pass

        self.write_api.write(bucket=self.bucket, record=point)

    def close(self):
        """Clean up connection."""
        self.client.close()
        print("[DB] Connection closed.")


# ── Test the connection ────────────────────────────────────
if __name__ == '__main__':
    logger = IDSDBLogger()
    print("[DB] Writing test point...")

    test_point = (
        Point("ids_prediction")
        .tag("prediction", "Test")
        .tag("is_attack", "False")
        .field("confidence", 0.99)
        .field("flow_number", 0)
        .field("attack_count", 0)
        .field("total_count", 1)
        .field("attack_rate", 0.0)
    )

    logger.write_api.write(bucket="network_traffic", record=test_point)
    print("[DB] Test point written successfully!")
    logger.close()