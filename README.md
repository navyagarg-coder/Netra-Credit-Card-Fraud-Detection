# Netra - Credit Card Fraud Detection System

<p align="center">
  <strong>Tuned XGBoost & Isolation Forest with Real-Time Web Dashboard</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-Web%20App-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/XGBoost-Supervised%20ML-189AB4?style=for-the-badge" alt="XGBoost">
  <img src="https://img.shields.io/badge/scikit--learn-1.6.1-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn">
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
</p>

---

## 🎯 Project Overview

**Netra** is an intelligent Machine Learning web application designed to evaluate credit card transactions in real time.

The system combines a **tuned XGBoost model** for supervised fraud probability estimation with an **Isolation Forest** for unsupervised anomaly scoring, helping security analysts filter out false positives and catch fraud instantly.

---

## 🎯 Problem Statement

Credit card fraud detection is a major challenge in financial systems due to extreme class imbalance (frauds make up only ~0.17% of total transactions). Traditional rule-based systems often miss complex non-linear fraud patterns or create excessive false alarms.

**Netra** provides an automated decision-support system that:

1. Ingests single or batch transaction records.
2. Preprocesses and scales feature inputs (`Time`, `Amount`, and V1 to V28).
3. Evaluates fraud probability via a tuned XGBoost classifier.
4. Generates an anomaly score using Isolation Forest.
5. Categorizes risk levels (LOW, MEDIUM, HIGH) based on threshold logic.
6. Flags suspicious transactions in an analyst review queue sorted by monetary impact.
7. Displays clear visual dashboards for financial monitoring.

---

## 💡 Key Features

### ⚡ Real-Time Transaction Predictor
Evaluate single transactions on demand with instant risk classification (LOW, MEDIUM, HIGH) and anomaly score visualization.

### 📡 Live Transaction Stream
Real-time simulated feed showing incoming payment traffic with automated flagging of suspicious transaction patterns.

### 📁 CSV Batch Processing
Upload bulk CSV datasets to score thousands of transactions simultaneously with downloadable summary reports.

### 📊 Interactive Analytics Dashboard
Visual metrics tracking total volume, fraud rates, risk distributions, and temporal trends.

### 🎯 Analyst Review Queue
Automatically prioritizes HIGH-risk alerts based on expected monetary loss for immediate analyst decision-making.

---

## 🧠 AI / ML Pipeline

```text
Transaction Input
      │
      ▼
Preprocessing & RobustScaling
      │
      ├───────────────────────────────┐
      ▼                               ▼
Parallel Scoring               Parallel Scoring
      │                               │
      ▼                               ▼
XGBoost Model                  IsoForest Model
      │                               │
      ▼                               ▼
  Fraud Prob                     Anomaly Score
      │                               │
      └───────────────┬───────────────┘
                      ▼
            Threshold Classification
             (LOW / MEDIUM / HIGH Risk)
                      │
                      ▼
           Flask UI & SQLite Database
```

---

## 🛠 Technologies Used

| Technology | Purpose |
| :--- | :--- |
| **Python 3.13** | Core language for machine learning & backend logic |
| **Flask** | Web framework & REST API endpoints |
| **XGBoost** | Tuned supervised classification model |
| **Scikit-learn** | Isolation Forest, RobustScaler, & metrics evaluation |
| **Pandas / NumPy** | Data manipulation and matrix operations |
| **SQLite** | Lightweight database for transaction history and logs |
| **HTML / CSS / JavaScript** | Responsive web dashboard and live stream frontend |
| **Joblib** | Model and scaler state serialization |
| **Git / GitHub** | Version control & reports posting |

---

## 📊 Model Performance

Evaluated on a held-out test set of **56,746 transactions**:

| Metric | Untuned XGBoost | Tuned XGBoost |
| :--- | :---: | :---: |
| **Precision** | 0.9259 | **0.9863** |
| **Recall** | 0.7895 | 0.7579 |
| **F1-Score** | 0.8523 | **0.8571** |
| **ROC-AUC** | 0.9631 | **0.9745** |
| **PR-AUC** | 0.8143 | **0.8157** |

---

## ⚙️ How It Works

1. **Preprocessing:** Scales `Time` and `Amount` using `RobustScaler` trained on training split data.
2. **Scoring:** Calculates fraud probability via XGBoost hyper-parameter tuned weights.
3. **Risk Categorization:**
   - **HIGH Risk:** Fraud Probability >= 0.9411
   - **MEDIUM Risk:** Fraud Probability between 0.3000 and 0.9411
   - **LOW Risk:** Fraud Probability < 0.3000

---

## 📁 Project Structure

```text
Netra-Credit-Card-Fraud-Detection/
├── app.py                  # Main Flask web application
├── make_live_pool.py       # Live stream transaction builder
├── data/
│   ├── live_pool.csv       # Stream transaction pool
│   ├── sample_fraud.csv    # Sample test data (Fraud)
│   └── sample_normal.csv   # Sample test data (Normal)
├── model/
│   ├── xgb_model.json      # Tuned XGBoost model weights
│   ├── scaler.pkl          # RobustScaler state
│   ├── iso_forest.pkl      # Trained Isolation Forest model
│   └── metrics.json        # Evaluation metadata & thresholds
├── modules/
│   ├── preprocessing.py    # Data cleaning & transformation
│   ├── predictor.py        # Model inference pipeline
│   ├── risk.py             # Threshold rules
│   ├── batch.py            # CSV file processor
│   └── database.py         # SQLite connection manager
├── screenshots/            # Dashboard application screenshots
│   ├── Screenshot 2026-10-01 155101.png
│   ├── Screenshot 2026-10-01 155123.png
│   ├── Screenshot 2026-10-01 155140.png
│   ├── Screenshot 2026-10-01 155202.png
│   └── Screenshot 2026-10-01 155230.png
├── static/                 # Stylesheets & client scripts
├── templates/              # Jinja2 HTML views
├── .gitignore
└── README.md
```

---

## 🏗 System Architecture

```text
                   ┌─────────────────┐
                   │ User / Analyst  │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Web Interface  │
                   │ (HTML + CSS + JS)│
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  Flask Backend  │
                   │   (Python 3)    │
                   └────────┬────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
 ┌─────────────────────┐         ┌─────────────────────┐
 │ Preprocessing Unit  │         │  SQLite Data Store  │
 │   (RobustScaler)    │         │  (History & Logs)   │
 └──────────┬──────────┘         └─────────────────────┘
            │
            ▼
 ┌─────────────────────┬─────────────────────┐
 │    XGBoost Model    │ Isolation Forest    │
 └──────────┬──────────┴──────────┬──────────┘
            │                     │
            └───────────┬─────────┘
                        ▼
             ┌─────────────────────┐
             │  Analyst Dashboard  │
             └─────────────────────┘
```

---

## 🔐 Limitations

- Trained on the ULB Kaggle dataset (V1–V28 PCA-transformed features).
- High-level decision threshold (0.9411) prioritizes high precision over high recall.
- Requires integration with active banking APIs for live production core-banking deployment.
- Offline SQLite storage is meant for demonstration and academic evaluation.

---

## 🔮 Future Scope

- 🌐 REST API expansion for external payment gateway integration.
- 🧠 Deep Learning models (Autoencoders / Graph Neural Networks) for sequence fraud detection.
- 👤 Cardholder behavioral profiling and transaction location anomaly matching.
- ☁ Production deployment on AWS/GCP with scalable PostgreSQL database.

---

## 🎓 Academic Context

| Field | Details |
| :--- | :--- |
| **Project** | Netra — Credit Card Fraud Detection System |
| | |
| **Student** | Navya Garg |
| **Branch / Year** | Computer Science & Engineering (3rd Year) |
| **Institute** | Dr. A.P.J. Abdul Kalam Technical University (AKTU) |

---

## 👨‍💻 Author

**Navya Garg**  
*B.Tech — Computer Science & Engineering*  
Dr. A.P.J. Abdul Kalam Technical University (AKTU)

---

## 📜 License

This project is developed for academic and demonstration purposes.

---

## 🖥️ Project Screenshots

### 🖼️️ Landing Page
![Landing Page](screenshots/Screenshot%202026-10-01%20155101.png)

### ✨ Features Overview
![Key Features](screenshots/Screenshot%202026-10-01%20155230.png)

### 📊 Fraud Monitoring Dashboard
![Dashboard](screenshots/Screenshot%202026-10-01%20155123.png)

### 📡 Live Payment Stream
![Live Monitor](screenshots/Screenshot%202026-10-01%20155202.png)

### 📈 Model Performance & Metrics
![Model Metrics](screenshots/Screenshot%202026-10-01%20155140.png)