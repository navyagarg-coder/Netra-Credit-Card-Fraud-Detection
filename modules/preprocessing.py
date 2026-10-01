import os
import joblib
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scaler = joblib.load(os.path.join(BASE, 'model', 'scaler.pkl'))

FEATURES = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount']


def preprocess(df):
    """Check columns, keep the right order, scale Time and Amount."""
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f'Missing columns: {missing}')

    df = df[FEATURES].copy()
    df = df.apply(pd.to_numeric, errors='raise')
    df[['Time', 'Amount']] = scaler.transform(df[['Time', 'Amount']])
    return df