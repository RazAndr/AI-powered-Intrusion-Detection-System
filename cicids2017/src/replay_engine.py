"""
Real-Time Network Traffic Replay Engine
Simulates live network traffic by replaying CICIDS2017 data
through the trained Random Forest model.

This is the core of the AI-powered IDS pipeline:
  Traffic → Preprocessing → Model → Prediction → (Database → Dashboard)
"""

import pandas as pd
import numpy as np
import joblib
import time
import sys
import os
from datetime import datetime

# ── Configuration ──────────────────────────────────────────
REPLAY_SPEED = 100  # flows per second (adjustable)
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'random_forest.joblib')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'scaler.joblib')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'target_encoder.joblib')
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'demo_replay.csv')


class IDSReplayEngine:
    """
    Loads the trained model and replays network traffic through it.
    Each flow gets a real-time prediction: Benign or Attack type.
    """

    def __init__(self):
        print("[IDS] Loading model and preprocessors...")
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        self.target_encoder = joblib.load(ENCODER_PATH)
        self.feature_names = self.scaler.feature_names_in_
        self.class_names = self.target_encoder.classes_

        print(f"[IDS] Model loaded: {len(self.class_names)} classes")
        print(f"[IDS] Features expected: {len(self.feature_names)}")
        print(f"[IDS] Classes: {list(self.class_names)}")

    def predict_batch(self, flows_df):
        """
        Predict on a batch of flows at once — much faster than one at a time.
        """
        features = flows_df[self.feature_names].copy()
        features = features.replace([np.inf, -np.inf], 0).fillna(0)

        features_scaled = pd.DataFrame(
            self.scaler.transform(features),
            columns=self.feature_names
        )

        predictions = self.model.predict(features_scaled)
        probabilities = self.model.predict_proba(features_scaled)

        results = []
        for i, (pred_idx, probs) in enumerate(zip(predictions, probabilities)):
            results.append({
                'prediction': self.class_names[pred_idx],
                'confidence': round(float(probs[pred_idx]), 4),
                'is_attack': self.class_names[pred_idx] != 'Benign'
            })

        return results

    def replay(self, data_path=None, speed=None, limit=None, callback=None):
        data_path = data_path or DATA_PATH
        speed = speed or REPLAY_SPEED

        print(f"\n[IDS] Loading traffic data from {os.path.basename(data_path)}...")
        df = pd.read_csv(data_path, low_memory=False)
        df.columns = df.columns.str.strip()

        if limit:
            df = df.head(limit)

        print(f"[IDS] Loaded {len(df)} flows. Starting replay at {speed} flows/sec...\n")

        stats = {
            'total': 0,
            'attacks': 0,
            'by_class': {name: 0 for name in self.class_names},
            'recent_attacks': []
        }

        batch_size = min(speed, 100)  # process in batches
        start_time = time.time()

        for batch_start in range(0, len(df), batch_size):
            batch = df.iloc[batch_start:batch_start + batch_size]
            results = self.predict_batch(batch)

            for i, result in enumerate(results):
                flow_num = batch_start + i + 1
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

                stats['total'] += 1
                stats['by_class'][result['prediction']] += 1
                if result['is_attack']:
                    stats['attacks'] += 1
                    stats['recent_attacks'].append(timestamp)

                result['flow_number'] = flow_num
                result['timestamp'] = timestamp

                if callback:
                    callback(flow_num, timestamp, batch.iloc[i], result, stats)
                else:
                    self._print_flow(flow_num, timestamp, result, stats)

            # Rate limiting per batch
            elapsed = time.time() - start_time
            expected = stats['total'] / speed
            if elapsed < expected:
                time.sleep(expected - elapsed)

        self._print_summary(stats, time.time() - start_time)
        return stats
    def _print_flow(self, flow_num, timestamp, result, stats):
        """Pretty-print a single flow prediction to console."""
        attack_rate = (stats['attacks'] / stats['total'] * 100) if stats['total'] > 0 else 0

        if result['is_attack']:
            # Red for attacks
            print(f"\033[91m[{timestamp}] Flow #{flow_num:>6d} │ "
                  f"⚠ {result['prediction']:20s} │ "
                  f"Confidence: {result['confidence']:.1%} │ "
                  f"Attacks: {stats['attacks']}/{stats['total']} ({attack_rate:.1f}%)\033[0m")
        else:
            # Green for benign — only print every 10th to reduce noise
            if flow_num % 10 == 0:
                print(f"\033[92m[{timestamp}] Flow #{flow_num:>6d} │ "
                      f"✓ {result['prediction']:20s} │ "
                      f"Confidence: {result['confidence']:.1%} │ "
                      f"Attacks: {stats['attacks']}/{stats['total']} ({attack_rate:.1f}%)\033[0m")

    def _print_summary(self, stats, elapsed):
        """Print final summary."""
        print(f"\n{'=' * 60}")
        print(f"REPLAY COMPLETE")
        print(f"{'=' * 60}")
        print(f"Total flows:  {stats['total']:,}")
        print(f"Attacks:      {stats['attacks']:,} ({stats['attacks'] / max(stats['total'], 1) * 100:.1f}%)")
        print(f"Duration:     {elapsed:.1f}s")
        print(f"Speed:        {stats['total'] / max(elapsed, 1):.0f} flows/sec")
        print(f"\nBreakdown:")
        for name, count in sorted(stats['by_class'].items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {name:20s}: {count:,}")


# ── Run directly ───────────────────────────────────────────
if __name__ == '__main__':
    engine = IDSReplayEngine()

    # Parse command line arguments
    limit = 500  # default: replay 500 flows for demo
    speed = 50  # default: 50 flows/sec

    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    if len(sys.argv) > 2:
        speed = int(sys.argv[2])

    print(f"\n[IDS] Starting replay: {limit} flows at {speed} flows/sec")
    print(f"[IDS] Press Ctrl+C to stop\n")

    try:
        engine.replay(speed=speed, limit=limit)
    except KeyboardInterrupt:
        print("\n[IDS] Stopped by user.")