"""
Full IDS Pipeline: Replay → Predict → Log to DB
This is the main entry point for the production system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from replay_engine import IDSReplayEngine
from db_logger import IDSDBLogger


def main():
    # Initialize components
    engine = IDSReplayEngine()
    db = IDSDBLogger()

    # Settings
    limit = 2000    # flows to process
    speed = 100     # flows per second

    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    if len(sys.argv) > 2:
        speed = int(sys.argv[2])

    print(f"\n[PIPELINE] Starting: {limit} flows at {speed}/sec")
    print(f"[PIPELINE] Predictions → InfluxDB → Grafana\n")

    def combined_callback(flow_num, timestamp, flow_data, result, stats):
        """Print to console AND write to database."""
        # Print to console
        engine._print_flow(flow_num, timestamp, result, stats)
        # Write to database
        db.log_prediction(flow_num, timestamp, flow_data, result, stats)

    try:
        engine.replay(speed=speed, limit=limit, callback=combined_callback)
    except KeyboardInterrupt:
        print("\n[PIPELINE] Stopped by user.")
    finally:
        db.close()
        print("[PIPELINE] Done.")


if __name__ == '__main__':
    main()