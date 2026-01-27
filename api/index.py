from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os
import yfinance as yf
import sys
from datetime import datetime

# Adjust path for Vercel subdirectory deployment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from us_market.daily_report_generator import USDailyReportGenerator

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
DATA_DIR = os.path.join(BASE_DIR, 'us_market')

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient='records')
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/us/smart-money')
def get_smart_money():
    data = load_csv('smart_money_picks_v2.csv')
    
    # Try to update top 10 with realtime prices
    try:
        top_tickers = [d['ticker'] for d in data[:10]]
        prices = yf.download(top_tickers, period='1d', interval='1m', progress=False)
        if not prices.empty:
            for d in data[:10]:
                ticker = d['ticker']
                try:
                    if isinstance(prices.columns, pd.MultiIndex):
                        current = prices['Close'][ticker].iloc[-1]
                    else:
                        current = prices['Close'].iloc[-1]
                    d['current_price'] = round(current, 2)
                except:
                    pass
    except Exception as e:
        print(f"Warning: Failed to update top prices: {e}")
        
    response = jsonify(data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/us/macro-analysis')
def get_macro_analysis():
    data = load_json('us_macro_analysis.json')
    return jsonify(data)

@app.route('/api/us/sector-heatmap')
def get_sector_heatmap():
    data = load_json('sector_heatmap.json')
    return jsonify(data)

@app.route('/api/us/options-flow')
def get_options_flow():
    data = load_json('options_flow.json')
    return jsonify(data)

@app.route('/api/us/economic-calendar')
def get_calendar():
    data = load_json('economic_calendar.json')
    return jsonify(data)

@app.route('/api/us/ai-summary/<ticker>')
def get_ai_summary(ticker):
    summaries = load_json('ai_stock_summaries.json')
    summary = summaries.get(ticker, "No summary available.")
    return jsonify({'ticker': ticker, 'summary': summary})

@app.route('/api/us/daily-report')
@app.route('/daily-report')
def get_daily_report():
    """Dynamically generate the daily report"""
    try:
        generator = USDailyReportGenerator(data_dir=DATA_DIR)
        html_content = generator.run()
        return html_content
    except Exception as e:
        return f"<h1>Error generating report</h1><p>{str(e)}</p>", 500

@app.route('/api/us/realtime-prices')
def get_realtime_prices():
    """Fetch realtime prices for watched tickers (limited)"""
    tickers = request.args.get('tickers', 'SPY,QQQ,NVDA,AAPL,TSLA').split(',')
    try:
        data = yf.download(tickers, period='1d', interval='1m', progress=False)
        prices = {}
        if not data.empty:
             for t in tickers:
                 try:
                     # Access using iloc for last row if MultiIndex
                     if isinstance(data.columns, pd.MultiIndex):
                         current = data['Close'][t].iloc[-1]
                         prev = data['Open'][t].iloc[0] # Approx change from open
                     else:
                         current = data['Close'].iloc[-1]
                         prev = data['Open'].iloc[0]
                     
                     change = ((current - prev) / prev) * 100
                     prices[t] = {
                         'price': round(current, 2),
                         'change': round(change, 2)
                     }
                 except: pass
        return jsonify(prices)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
