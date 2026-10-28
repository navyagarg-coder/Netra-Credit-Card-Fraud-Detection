import os
import json
import math
import uuid
import random
from functools import lru_cache

import pandas as pd
from flask import (Flask, render_template, request, Response, redirect,
                   jsonify, session)

from modules.preprocessing import FEATURES
from modules.predictor import predict_one
from modules.batch import predict_csv
from modules.database import (save_prediction, get_history, get_stats, get_review_queue,
                              update_review, get_trend, get_risk_counts, get_top_suspicious,
                              get_review_counts)

app = Flask(__name__)
# Needed so each browser gets its own session (used for the CSV download).
app.secret_key = os.environ.get('NETRA_SECRET', 'change-this-secret-before-deploying')
# Block uploads bigger than 5 MB.
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# ---------- startup check ----------
POOL_PATH = os.path.join('data', 'live_pool.csv')
if not os.path.exists(POOL_PATH):
    raise SystemExit(
        'data/live_pool.csv is missing.\n'
        'Put creditcard.csv inside the data/ folder and run:  python make_live_pool.py'
    )

POOL = pd.read_csv(POOL_PATH)
NORMAL_POOL = POOL[POOL['Class'] == 0]
FRAUD_POOL = POOL[POOL['Class'] == 1]

# Last uploaded result for EACH user (key = their session id).
LAST = {}


def _user_id():
    if 'rid' not in session:
        session['rid'] = uuid.uuid4().hex
    return session['rid']


# ---------- cached file readers ----------
@lru_cache(maxsize=1)
def _metrics_cached():
    with open(os.path.join('model', 'metrics.json')) as f:
        return json.load(f)


def load_metrics():
    # Note: if you retrain and change metrics.json, restart the app.
    return _metrics_cached()


@lru_cache(maxsize=None)
def _sample_cached(name):
    return pd.read_csv(f'data/{name}.csv').iloc[0].to_dict()


def load_sample(name):
    return dict(_sample_cached(name))


# ---------- pages ----------
@app.route('/')
def home():
    return render_template('landing.html', m=load_metrics())


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    result, error = None, None
    if request.method == 'POST':
        try:
            row = {f: float(request.form[f]) for f in FEATURES}
            # reject nan / inf
            if not all(math.isfinite(v) for v in row.values()):
                raise ValueError('not finite')
            result = predict_one(row)
            save_prediction(row['Amount'], result['prediction'],
                            result['probability'], result['risk_level'])
        except (ValueError, KeyError):
            error = 'Please fill all 30 fields with valid numbers only.'
    return render_template('predict.html', features=FEATURES, result=result, error=error,
                           fraud_sample=load_sample('sample_fraud'),
                           normal_sample=load_sample('sample_normal'))


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    rows, summary, error = None, None, None
    if request.method == 'POST':
        f = request.files.get('file')
        if not f or f.filename == '':
            error = 'Please choose a CSV file.'
        else:
            try:
                result, summary = predict_csv(f)
                LAST[_user_id()] = result
                rows = result[['Amount', 'fraud_probability', 'prediction',
                               'risk_level']].head(200).to_dict('records')
            except ValueError as e:
                error = str(e)
    return render_template('upload.html', rows=rows, summary=summary, error=error)


@app.errorhandler(413)
def file_too_big(e):
    return render_template('upload.html', rows=None, summary=None,
                           error='File is too large. Maximum size is 5 MB.'), 413


@app.route('/download')
def download():
    df = LAST.get(session.get('rid'))
    if df is None:
        return 'No results yet. Upload a file first.', 404
    return Response(df.to_csv(index=False), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=netra_results.csv'})


@app.route('/sample.csv')
def sample_csv():
    df = pd.concat([pd.read_csv('data/sample_fraud.csv'), pd.read_csv('data/sample_normal.csv')])
    return Response(df.to_csv(index=False), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=netra_sample.csv'})


@app.route('/history')
def history():
    return render_template('history.html', rows=get_history(1000))


@app.route('/dashboard')
def dashboard():
    trend = get_trend()
    mx = max([t['total'] for t in trend], default=1)
    for t in trend:
        t['h'] = round(100 * t['total'] / mx)
        t['fh'] = round(100 * t['fraud'] / mx)
    rc = get_risk_counts()
    tot = sum(rc.values()) or 1
    risk = [{'name': k.title(), 'key': k.lower(), 'n': v, 'pct': round(100 * v / tot)}
            for k, v in rc.items()]
    return render_template('dashboard.html', stats=get_stats(), trend=trend,
                           recent=get_history(8), top=get_top_suspicious(5),
                           risk=risk, m=load_metrics())


@app.route('/review', methods=['GET', 'POST'])
def review():
    if request.method == 'POST':
        try:
            update_review(int(request.form['id']), request.form['status'])
        except (ValueError, KeyError):
            pass
        return redirect('/review')
    rows = get_review_queue()
    for r in rows:
        r['loss'] = round(r['amount'] * r['probability'], 2)
    rows.sort(key=lambda r: r['loss'], reverse=True)
    return render_template('review.html', rows=rows, c=get_review_counts())


@app.route('/performance')
def performance():
    return render_template('performance.html', m=load_metrics())


@app.route('/live')
def live():
    return render_template('live.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'threshold': load_metrics()['threshold']})


@app.route('/api/simulate')
def simulate():
    pool = FRAUD_POOL if random.random() < 0.10 else NORMAL_POOL
    row = pool.sample(1).iloc[0].drop('Class').to_dict()
    result = predict_one(row)
    save_prediction(row['Amount'], result['prediction'],
                    result['probability'], result['risk_level'],
                    source='live')  # CHANGED: mark these rows as live-stream rows
    return jsonify({'amount': round(float(row['Amount']), 2), **result})


if __name__ == '__main__':
    # Debug is OFF by default. To turn it on while developing:
    #   Windows (PowerShell):  $env:FLASK_DEBUG="1"; python app.py
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')