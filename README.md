# AI-Powered Network Traffic Anomaly & Attack Detector

An Intrusion Detection System (IDS) that uses machine learning to detect malicious network traffic (DDoS, port scans, malware communication) in real-time.

## Features
- Random Forest classifier trained on NSL-KDD dataset
- Real-time traffic replay engine for simulation
- InfluxDB logging with Grafana SOC dashboard
- Automated Discord/Telegram alerts on attack spikes

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Download NSL-KDD dataset into data/
# https://www.unb.ca/cic/datasets/nsl.html
```

## Project Structure
```
ids-project/
├── data/                  # NSL-KDD dataset files
├── notebooks/             # Jupyter notebooks (Phases 1-4)
├── src/                   # Production pipeline (Phases 5-8)
├── models/                # Saved trained models
├── config/                # Configuration files
├── requirements.txt
└── README.md
```

## Build Phases
1. Data Loading & Exploration
2. Preprocessing & Feature Engineering
3. Train Random Forest Classifier
4. Evaluation & Handling Imbalance
5. Real-Time Replay Engine
6. Database Logging Layer
7. Grafana SOC Dashboard
8. Alert System

## Dataset
NSL-KDD — an improved version of the original KDD Cup 1999 dataset, commonly used for IDS research.
- `KDDTrain+.txt` — 125,973 records for training
- `KDDTest+.txt` — 22,544 records for testing
