import os
import json
import random
import pandas as pd
from flask import Flask, render_template, request, Response, redirect, jsonify
from modules.preprocessing import FEATURES
from modules.predictor import predict_one
from modules.batch import predict_csv
from modules.database import (save_prediction, get_history, get_stats, get_review_queue,
                              update_review, get_trend, get_risk_counts, get_top_suspicious,
                              get_review_counts)

app = Flask(__name__)
LAST = {'df': None}

POOL = pd.read_csv('data/live_pool.csv')
NORMAL_POOL = POOL[POOL['Class'] == 0]
FRAUD_POOL = POOL[POOL['Class'] == 1]


def load_sample(name):
    return pd.read_csv(f'data/{name}.csv').iloc[0].to_dict()


def load_metrics():
    with open(os.path.join('model', 'metrics.json')) as f:
        return json.load(f)

@app.route('/')
def home():
    return render_template('landing.html', m=load_metrics())


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    result, error = None, None
    if request.method == 'POST':
        try:
            row = {f: float(request.form[f]) for f in FEATURES}
            result = predict_one(row)
            save_prediction(row['Amount'], result['prediction'],
                            result['probability'], result['risk_level'])
        except (ValueError, KeyError):
            error = 'Please fill all 30 fields with numbers only.'
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
                LAST['df'] = result
                rows = result[['Amount', 'fraud_probability', 'prediction',
                               'risk_level']].head(200).to_dict('records')
            except ValueError as e:
                error = str(e)
    return render_template('upload.html', rows=rows, summary=summary, error=error)


@app.route('/download')
def download():
    if LAST['df'] is None:
        return 'No results yet. Upload a file first.', 404
    return Response(LAST['df'].to_csv(index=False), mimetype='text/csv',
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
                    result['probability'], result['risk_level'])
    return jsonify({'amount': round(float(row['Amount']), 2), **result})


if __name__ == '__main__':
    app.run(debug=True)