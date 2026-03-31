"""
AI-Powered IDS — Full Demo
Runs the complete pipeline: Replay → Predict → Database → Dashboard

Prerequisites:
  - Docker running with InfluxDB (port 8086) and Grafana (port 3000)
  - InfluxDB bucket 'network_traffic' created
  - Grafana dashboard configured

Usage:
  python demo.py              # default: 2000 flows at 100/sec
  python demo.py 5000 200     # custom: 5000 flows at 200/sec
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from replay_engine import IDSReplayEngine
from db_logger import IDSDBLogger


def main():
    print("=" * 60)
    print("  AI-POWERED INTRUSION DETECTION SYSTEM")
    print("  Real-Time Network Traffic Analysis Demo")
    print("=" * 60)

    # Parse arguments
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    speed = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    # Initialize
    print("\n[1/3] Loading AI model...")
    engine = IDSReplayEngine()

    print("[2/3] Connecting to InfluxDB...")
    try:
        db = IDSDBLogger()
        db_connected = True
    except Exception as e:
        print(f"[WARNING] Could not connect to InfluxDB: {e}")
        print("[WARNING] Running without database logging.")
        print("[WARNING] Start InfluxDB with: docker start influxdb")
        db_connected = False

    print(f"[3/3] Starting replay: {limit} flows at {speed}/sec")
    print(f"\n{'=' * 60}")
    print(f"  Open Grafana at http://localhost:3000 to see live dashboard")
    print(f"{'=' * 60}\n")

    def callback(flow_num, timestamp, flow_data, result, stats):
        engine._print_flow(flow_num, timestamp, result, stats)
        if db_connected:
            db.log_prediction(flow_num, timestamp, flow_data, result, stats)

    try:
        engine.replay(speed=speed, limit=limit, callback=callback)
    except KeyboardInterrupt:
        print("\n[IDS] Stopped by user.")
    finally:
        if db_connected:
            db.close()

    print("\n[DEMO] Complete. Check your Grafana dashboard for results.")


if __name__ == '__main__':
    main()