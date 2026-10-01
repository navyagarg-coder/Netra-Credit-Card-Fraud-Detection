import pandas as pd
from modules.predictor import predict_df
from modules.database import save_many


def predict_csv(file, save=True):
    """Read a CSV, predict every row, save to history, return (table, summary)."""
    try:
        df = pd.read_csv(file)
    except Exception:
        raise ValueError('Could not read the file. Please upload a valid CSV.')

    if df.empty:
        raise ValueError('The CSV file is empty.')

    result = predict_df(df)

    if save:
        save_many(list(zip(result['Amount'], result['prediction'],
                           result['fraud_probability'], result['risk_level'])))

    total = len(result)
    fraud = int((result['prediction'] == 'FRAUD').sum())
    summary = {
        'total': total,
        'fraud': fraud,
        'normal': total - fraud,
        'fraud_percent': round(100 * fraud / total, 2),
        'high_risk': int((result['risk_level'] == 'HIGH').sum()),
    }
    return result, summary