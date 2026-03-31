"""Create a small mixed dataset for replay demos."""
import pandas as pd
import os

data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cicids2017_clean.csv')
output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'demo_replay.csv')

print("Loading full dataset...")
df = pd.read_csv(data_path, low_memory=False)
df.columns = df.columns.str.strip()

print("Sampling a mix of benign and attacks...")
# Take 5000 benign and up to 1000 of each attack type
samples = []
samples.append(df[df['Label'] == 'BENIGN'].sample(n=5000, random_state=42))

for label in df['Label'].unique():
    if label != 'BENIGN':
        attack_data = df[df['Label'] == label]
        n = min(1000, len(attack_data))
        samples.append(attack_data.sample(n=n, random_state=42))

demo = pd.concat(samples).sample(frac=1, random_state=42)  # shuffle
demo.to_csv(output_path, index=False)

print(f"Demo dataset: {len(demo)} rows")
print(f"Label distribution:")
print(demo['Label'].value_counts())
print(f"\nSaved to {output_path}")