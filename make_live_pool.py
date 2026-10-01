import pandas as pd

df = pd.read_csv('data/creditcard.csv')
df = df.drop_duplicates()

normal = df[df['Class'] == 0].sample(1500, random_state=1)
fraud = df[df['Class'] == 1].sample(150, random_state=1)
pool = pd.concat([normal, fraud]).sample(frac=1, random_state=1)

pool.to_csv('data/live_pool.csv', index=False)
print('Created live_pool.csv with', len(pool), 'rows')
print('Max Amount:', pool['Amount'].max())