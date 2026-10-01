import pandas as pd
from modules.predictor import predict_df, predict_one

for name in ['sample_fraud', 'sample_normal']:
    df = pd.read_csv(f'data/{name}.csv')
    print(name)
    print(predict_df(df)[['fraud_probability', 'prediction', 'risk_level']])
    print()

# single prediction test
row = pd.read_csv('data/sample_fraud.csv').iloc[0].to_dict()
print('Single:', predict_one(row))

# wrong input test (should show a clean error)
try:
    predict_df(pd.DataFrame({'Amount': [10]}))
except ValueError as e:
    print('Error handled:', e)