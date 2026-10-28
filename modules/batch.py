import pandas as pd
from modules.predictor import predict_df
from modules.database import save_many


def predict_csv(file, save=True):
    """Read a CSV, predict every row, save suspicious rows, return (table, summary)."""
    try:
        df = pd.read_csv(file)
    except Exception:
        raise ValueError('Could not read the file. Please upload a valid CSV.')

    if df.empty:
        raise ValueError('The CSV file is empty.')

    result = predict_df(df)

    saved = 0
    if save:
        # Only MEDIUM and HIGH rows are stored. LOW rows are not useful to keep,
        # and storing thousands of them would flood the history page.
        keep = result[result['risk_level'] != 'LOW']
        rows = list(zip(keep['Amount'], keep['prediction'],
                        keep['fraud_probability'], keep['risk_level']))
        save_many(rows, source='batch')
        saved = len(rows)

    total = len(result)
    fraud = int((result['prediction'] == 'FRAUD').sum())
    summary = {
        'total': total,
        'fraud': fraud,
        'normal': total - fraud,
        'fraud_percent': round(100 * fraud / total, 2),
        'high_risk': int((result['risk_level'] == 'HIGH').sum()),
        'saved': saved,
    }
    return result, summary