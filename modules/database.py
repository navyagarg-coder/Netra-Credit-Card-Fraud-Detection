import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, 'database', 'fraud.db')

# Dashboard numbers ignore rows that came from CSV uploads.
NOT_BATCH = "COALESCE(source, 'manual') != 'batch'"

_READY = False


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db():
    """Open a connection, save changes, always close it."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the table, upgrade an old table, add indexes. Runs only once."""
    global _READY
    if _READY:
        return
    with db() as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            prediction TEXT,
            probability REAL,
            risk_level TEXT,
            review_status TEXT,
            created_at TEXT,
            source TEXT DEFAULT 'manual',
            reviewed_at TEXT)''')

        # Upgrade an older database that does not have the new columns yet
        cols = [r['name'] for r in conn.execute('PRAGMA table_info(transactions)')]
        if 'source' not in cols:
            conn.execute("ALTER TABLE transactions ADD COLUMN source TEXT DEFAULT 'manual'")
        if 'reviewed_at' not in cols:
            conn.execute('ALTER TABLE transactions ADD COLUMN reviewed_at TEXT')

        # Indexes make searching and sorting fast
        conn.execute('CREATE INDEX IF NOT EXISTS idx_review ON transactions(review_status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON transactions(created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_prob ON transactions(probability)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON transactions(source)')
    _READY = True


def _status_for(risk_level):
    return 'Pending' if risk_level == 'HIGH' else 'Not needed'


def save_many(rows, source='manual'):
    """rows = list of (amount, prediction, probability, risk_level)."""
    if not rows:
        return
    init_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = [(a, p, pr, r, _status_for(r), now, source) for a, p, pr, r in rows]
    with db() as conn:
        conn.executemany(
            'INSERT INTO transactions '
            '(amount, prediction, probability, risk_level, review_status, created_at, source) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)', data)


def save_prediction(amount, prediction, probability, risk_level, source='manual'):
    save_many([(amount, prediction, probability, risk_level)], source=source)


def get_history(limit=100):
    init_db()
    with db() as conn:
        rows = conn.execute('SELECT * FROM transactions ORDER BY id DESC LIMIT ?',
                            (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_review_queue():
    init_db()
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE review_status = 'Pending' ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_review(transaction_id, status):
    """status must be 'Confirmed Fraud' or 'False Alarm'."""
    if status not in ('Confirmed Fraud', 'False Alarm'):
        raise ValueError('Status must be Confirmed Fraud or False Alarm')
    init_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db() as conn:
        conn.execute('UPDATE transactions SET review_status = ?, reviewed_at = ? WHERE id = ?',
                     (status, now, transaction_id))


def get_stats():
    init_db()
    with db() as conn:
        row = conn.execute(f'''SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN prediction = 'FRAUD' THEN 1 ELSE 0 END) AS fraud,
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) AS high_risk
            FROM transactions WHERE {NOT_BATCH}''').fetchone()
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
    with db() as conn:
        rows = conn.execute(f'''SELECT substr(created_at, 1, 10) AS day,
            COUNT(*) AS total,
            SUM(CASE WHEN prediction = 'FRAUD' THEN 1 ELSE 0 END) AS fraud
            FROM transactions WHERE {NOT_BATCH}
            GROUP BY day ORDER BY day DESC LIMIT ?''', (days,)).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_risk_counts():
    init_db()
    with db() as conn:
        rows = conn.execute(f'''SELECT risk_level, COUNT(*) AS n FROM transactions
                                WHERE {NOT_BATCH} GROUP BY risk_level''').fetchall()
    d = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for r in rows:
        d[r['risk_level']] = r['n']
    return d


def get_top_suspicious(limit=5):
    init_db()
    with db() as conn:
        rows = conn.execute(f'''SELECT * FROM transactions WHERE {NOT_BATCH}
                                ORDER BY probability DESC, amount DESC LIMIT ?''',
                            (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_review_counts():
    init_db()
    with db() as conn:
        rows = conn.execute('''SELECT review_status, COUNT(*) AS n FROM transactions
                               GROUP BY review_status''').fetchall()
        loss = conn.execute('''SELECT COALESCE(SUM(amount * probability), 0) AS s
                               FROM transactions WHERE review_status = 'Pending' ''').fetchone()['s']
    c = {r['review_status']: r['n'] for r in rows}
    return {'pending': c.get('Pending', 0), 'confirmed': c.get('Confirmed Fraud', 0),
            'false_alarm': c.get('False Alarm', 0), 'loss': round(loss, 2)}


# Create / upgrade the database as soon as the app starts
init_db()