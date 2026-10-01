import os
import sqlite3
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, 'database', 'fraud.db')


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL,
        prediction TEXT,
        probability REAL,
        risk_level TEXT,
        review_status TEXT,
        created_at TEXT)''')
    conn.commit()
    conn.close()


def _status_for(risk_level):
    return 'Pending' if risk_level == 'HIGH' else 'Not needed'


def save_many(rows):
    """rows = list of (amount, prediction, probability, risk_level)."""
    init_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = [(a, p, pr, r, _status_for(r), now) for a, p, pr, r in rows]
    conn = get_conn()
    conn.executemany(
        'INSERT INTO transactions (amount, prediction, probability, risk_level, review_status, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?)', data)
    conn.commit()
    conn.close()


def save_prediction(amount, prediction, probability, risk_level):
    save_many([(amount, prediction, probability, risk_level)])


def get_history(limit=100):
    init_db()
    conn = get_conn()
    rows = conn.execute('SELECT * FROM transactions ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_review_queue():
    init_db()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE review_status = 'Pending' ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_review(transaction_id, status):
    """status must be 'Confirmed Fraud' or 'False Alarm'."""
    if status not in ('Confirmed Fraud', 'False Alarm'):
        raise ValueError('Status must be Confirmed Fraud or False Alarm')
    conn = get_conn()
    conn.execute('UPDATE transactions SET review_status = ? WHERE id = ?', (status, transaction_id))
    conn.commit()
    conn.close()


def get_stats():
    init_db()
    conn = get_conn()
    row = conn.execute('''SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN prediction = 'FRAUD' THEN 1 ELSE 0 END) AS fraud,
        SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk
        FROM transactions''').fetchone()
    conn.close()
    total = row['total'] or 0
    fraud = row['fraud'] or 0
    return {
        'total': total,
        'fraud': fraud,
        'normal': total - fraud,
        'fraud_percent': round(100 * fraud / total, 2) if total else 0,
        'high_risk': row['high_risk'] or 0,
    }
def get_trend(days=7):
    """Transactions and fraud count per day (for the dashboard chart)."""
    init_db()
    conn = get_conn()
    rows = conn.execute('''SELECT substr(created_at, 1, 10) AS day,
        COUNT(*) AS total,
        SUM(CASE WHEN prediction = 'FRAUD' THEN 1 ELSE 0 END) AS fraud
        FROM transactions GROUP BY day ORDER BY day DESC LIMIT ?''', (days,)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def get_risk_counts():
    init_db()
    conn = get_conn()
    rows = conn.execute('SELECT risk_level, COUNT(*) AS n FROM transactions GROUP BY risk_level').fetchall()
    conn.close()
    d = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for r in rows:
        d[r['risk_level']] = r['n']
    return d


def get_top_suspicious(limit=5):
    init_db()
    conn = get_conn()
    rows = conn.execute('SELECT * FROM transactions ORDER BY probability DESC, amount DESC LIMIT ?',
                        (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_review_counts():
    init_db()
    conn = get_conn()
    rows = conn.execute('SELECT review_status, COUNT(*) AS n FROM transactions GROUP BY review_status').fetchall()
    loss = conn.execute("SELECT COALESCE(SUM(amount * probability), 0) AS s FROM transactions "
                        "WHERE review_status = 'Pending'").fetchone()['s']
    conn.close()
    c = {r['review_status']: r['n'] for r in rows}
    return {'pending': c.get('Pending', 0), 'confirmed': c.get('Confirmed Fraud', 0),
            'false_alarm': c.get('False Alarm', 0), 'loss': round(loss, 2)}