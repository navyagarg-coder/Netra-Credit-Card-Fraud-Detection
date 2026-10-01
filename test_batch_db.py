from modules.batch import predict_csv
from modules.database import get_history, get_review_queue, update_review, get_stats

_, s = predict_csv('data/sample_fraud.csv')
print('Fraud file  :', s)
_, s = predict_csv('data/sample_normal.csv')
print('Normal file :', s)

print('History rows:', len(get_history()))

queue = get_review_queue()
print('Review queue:', len(queue))
if queue:
    update_review(queue[0]['id'], 'Confirmed Fraud')
    print('Queue after 1 review:', len(get_review_queue()))

print('Stats:', get_stats())

try:
    predict_csv('data/no_such_file.csv')
except ValueError as e:
    print('Error handled:', e)