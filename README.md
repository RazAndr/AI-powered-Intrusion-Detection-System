# AI-Powered Network Intrusion Detection System

A machine learning-based Intrusion Detection System (IDS) that detects malicious network traffic in real-time using Random Forest classification, with live monitoring via a Grafana SOC dashboard.

## Architecture

```
Network Traffic → AI Model → InfluxDB → Grafana Dashboard
     (CSV)        (Random     (Time-      (Real-time
                  Forest)     series DB)   visualization)
```

## Features

- **Real-time detection** of 7 attack categories: DoS/DDoS, Brute Force, Web Attacks, Reconnaissance, Botnet, Infiltration
- **99.89% accuracy** on CICIDS2017 dataset (within-dataset evaluation)
- **Live SOC dashboard** with threat gauge, attack timeline, and attack type distribution
- **Cross-dataset analysis** revealing domain shift limitations (tested against CICIDS2018)
- **NSL-KDD benchmark** included as foundational research with documented limitations

## Project Structure

```
├── nsl-kdd/                        # Foundational research (Phases 1-4)
│   ├── notebooks/
│   │   ├── phase1_exploration.ipynb
│   │   ├── phase2_preprocessing.ipynb
│   │   ├── phase3_training.ipynb
│   │   └── phase4_evaluation.ipynb
│   ├── models/
│   │   ├── random_forest.joblib
│   │   ├── random_forest_smote.joblib
│   │   ├── encoders.joblib
│   │   ├── scaler.joblib
│   │   └── target_encoder.joblib
│   └── data/
│       ├── KDDTrain+.txt
│       └── KDDTest+.txt
│
├── cicids2017/                     # Production pipeline (Phases 1-7)
│   ├── notebooks/
│   │   ├── phase1_exploration.ipynb
│   │   ├── phase2_preprocessing.ipynb
│   │   ├── phase3_training.ipynb
│   │   ├── phase4_evaluation.ipynb
│   │   └── cross-dataset TEST.ipynb
│   ├── models/
│   │   ├── random_forest.joblib
│   │   ├── scaler.joblib
│   │   └── target_encoder.joblib
│   ├── src/
│   │   ├── replay_engine.py        # Real-time traffic simulation
│   │   ├── db_logger.py            # InfluxDB writer
│   │   ├── run_pipeline.py         # Full pipeline runner
│   │   ├── demo.py                 # Demo entry point
│   │   └── create_demo_data.py     # Demo dataset generator
│   └── data/
│       └── (CICIDS2017 CSVs — download separately)
│
├── README.md
├── requirements.txt
└── .gitignore
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker Desktop

### 1. Clone and install

```bash
git clone https://github.com/RazAndr/AI-powered-Intrusion-Detection-System.git
cd AI-powered-Intrusion-Detection-System
pip install -r requirements.txt
```

### 2. Download the CICIDS2017 dataset

Download from [Kaggle](https://www.kaggle.com/datasets/cicdataset/cicids2017) and place all CSV files in `cicids2017/data/`.

### 3. Start the infrastructure

```bash
docker run -d --name influxdb -p 8086:8086 -v influxdb-data:/var/lib/influxdb2 influxdb:2
docker run -d --name grafana -p 3000:3000 -v grafana-data:/var/lib/grafana grafana/grafana
```

Set up InfluxDB at `http://localhost:8086`:
- Organization: `idsproject`
- Bucket: `network_traffic`
- Save the API token and update it in `cicids2017/src/db_logger.py`

Set up Grafana at `http://localhost:3000`:
- Add InfluxDB data source (Flux query language)
- URL: `http://host.docker.internal:8086`

### 4. Generate demo data and run

```bash
cd cicids2017
python src/create_demo_data.py
python src/demo.py 2000 100
```

Open `http://localhost:3000` to see the live SOC dashboard updating in real-time.

## Datasets

| Dataset | Year | Records | Use |
|---------|------|---------|-----|
| NSL-KDD | 2009 | 125K | Foundational research, documented limitations |
| CICIDS2017 | 2017 | 2.8M | Production model training and evaluation |
| CICIDS2018 | 2018 | 16M | Cross-dataset generalization testing |

## Model Performance

### Within-Dataset (CICIDS2017)

| Class | Precision | Recall | F1-Score |
|-------|-----------|--------|----------|
| Benign | 1.00 | 1.00 | 1.00 |
| DoS/DDoS | 1.00 | 1.00 | 1.00 |
| Brute Force | 1.00 | 1.00 | 1.00 |
| Reconnaissance | 0.99 | 1.00 | 0.99 |
| Web Attack | 0.99 | 0.97 | 0.98 |
| Botnet | 0.90 | 0.74 | 0.81 |
| Infiltration | 1.00 | 0.43 | 0.60 |

**Overall accuracy: 99.89% | Macro F1: 0.91**

### Cross-Dataset (CICIDS2017 → CICIDS2018)

| Direction | Accuracy | Macro F1 |
|-----------|----------|----------|
| 2017 → 2017 (within) | 99.89% | 0.910 |
| 2018 → 2018 (within) | 99.00% | 0.990 |
| 2017 → 2018 (cross) | 89.26% | 0.236 |
| 2018 → 2017 (cross) | 85.00% | 0.229 |

The model collapses on cross-dataset testing, predicting almost everything as Benign. This is consistent with published research by Cantone et al. (2024) on cross-dataset generalization in ML-based NIDS.

### Root Cause Analysis

Feature analysis revealed the core problem: the model's top features (packet sizes, backward segment sizes) are **network-specific**, not attack-specific. For example:

- **CICIDS2017 DDoS** (Hulk/GoldenEye): Large, varied packets with high `Bwd Packet Length Max`
- **CICIDS2018 DDoS** (LOIC-HTTP): Small, uniform HTTP requests with low `Bwd Packet Length Max`

Same attack category, completely different feature fingerprint. The model learned "big packets = DDoS" but 2018's DDoS uses small packets.

Engineered ratio features (`fwd_byte_ratio`, `fwd_bwd_size_ratio`) showed near-zero shift between datasets (0.001-0.009) compared to raw features (shift of 2.0+), but were still insufficient to overcome the generalization gap with a Random Forest classifier.

### NSL-KDD Results

| Class | F1-Score | Notes |
|-------|----------|-------|
| DoS | 0.854 | Strong |
| Normal | 0.775 | Good |
| Probe | 0.728 | Good |
| R2L | 0.045 | Poor — 17 unseen attack types in test set |
| U2R | 0.195 | Limited — only 52 training samples |

## Key Findings

1. **ML-based IDS achieves near-perfect detection on its training network** but fails to generalize across different network environments.

2. **Domain shift is the core challenge.** Different attack tools produce fundamentally different traffic fingerprints even for the same attack category.

3. **The cross-dataset generalization problem is symmetric** — training on either dataset and testing on the other produces equally poor results.

4. **Feature engineering alone cannot solve the generalization problem.** Even network-invariant ratio features failed to transfer with a tree-based classifier that memorizes exact split thresholds.

5. **Practical implication:** Production IDS systems must be trained on the specific network they protect and retrained periodically as traffic patterns evolve.

## Future Work

- **Domain-Adversarial Neural Networks (DANN):** Force the feature extractor to learn only attack-specific patterns by training against a domain classifier.
- **Few-shot adaptation:** Fine-tune the pre-trained model on ~50-100 labeled flows from a new target network.
- **Contrastive learning:** Train embeddings where same-type attacks cluster together regardless of source network.
- **Alert system:** Automated Discord/Telegram notifications when attack density exceeds a configurable threshold.

## Tech Stack

- **ML:** Python, Scikit-learn, Pandas, NumPy, Matplotlib, Seaborn
- **Database:** InfluxDB 2.x (time-series)
- **Dashboard:** Grafana
- **Infrastructure:** Docker
- **Datasets:** CICIDS2017, CICIDS2018, NSL-KDD

## References

- Sharafaldin, I., Lashkari, A.H., & Ghorbani, A.A. (2018). "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization." 4th International Conference on Information Systems Security and Privacy (ICISSP).
- Cantone, M., Marrocco, C., & Bria, A. (2024). "Machine Learning in Network Intrusion Detection: A Cross-Dataset Generalization Study." IEEE Access, 12, 144489-144508.
- Tavallaee, M., Bagheri, E., Lu, W., & Ghorbani, A. (2009). "A Detailed Analysis of the KDD CUP 99 Data Set." Second IEEE Symposium on Computational Intelligence for Security and Defense Applications (CISDA).