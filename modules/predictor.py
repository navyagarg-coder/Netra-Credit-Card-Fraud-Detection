import os
import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from modules.preprocessing import preprocess
from modules.risk import get_risk_level

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = XGBClassifier()
model.load_model(os.path.join(BASE, 'model', 'xgb_model.json'))
_metrics = json.load(open(os.path.join(BASE, 'model', 'metrics.json')))
THRESHOLD = _metrics['threshold']

iso = joblib.load(os.path.join(BASE, 'model', 'iso_forest.pkl'))
LO, HI = _metrics['anomaly']['score_lo'], _metrics['anomaly']['score_hi']


def predict_df(df):
    """Predict many transactions. Adds probability, prediction, risk and anomaly info."""
    X = preprocess(df)
    probs = model.predict_proba(X)[:, 1]

    raw = -iso.score_samples(X)
    anomaly_score = np.clip((raw - LO) / (HI - LO), 0, 1) * 100
    anomaly_flag = iso.predict(X) == -1

    out = df.copy()
    out['fraud_probability'] = probs.round(4)
    out['prediction'] = ['FRAUD' if p >= THRESHOLD else 'NORMAL' for p in probs]
    out['risk_level'] = [get_risk_level(p, THRESHOLD) for p in probs]
    out['anomaly_score'] = anomaly_score.round(1)
    out['anomaly_flag'] = ['UNUSUAL' if a else 'USUAL' for a in anomaly_flag]
    return out


def predict_one(row_dict):
    """Predict one transaction (a dictionary of the 30 values)."""
    r = predict_df(pd.DataFrame([row_dict])).iloc[0]
    return {
        'prediction': r['prediction'],
        'probability': float(r['fraud_probability']),
        'risk_level': r['risk_level'],
        'anomaly_score': float(r['anomaly_score']),
        'anomaly_flag': r['anomaly_flag'],
    }