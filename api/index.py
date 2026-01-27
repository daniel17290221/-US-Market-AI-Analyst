from flask import Flask, render_template, jsonify, request
import csv
import json
import os
import requests
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
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"Error loading CSV {filename}: {e}")
    return []

def fetch_realtime_data(tickers):
    """Manual fetch for Yahoo Finance (Lightweight replacement for yfinance)"""
    prices = {}
    for ticker in tickers:
        if not ticker: continue
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=5)
            data = resp.json()
            
            if 'quoteResponse' in data and data['quoteResponse']['result']:
                quote = data['quoteResponse']['result'][0]
                prices[ticker] = {
                    'price': round(quote.get('regularMarketPrice', 0), 2),
                    'change': round(quote.get('regularMarketChangePercent', 0), 2)
                }
        except:
            pass
    return prices

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/us/smart-money')
def get_smart_money():
    data = load_csv('smart_money_picks_v2.csv')
    
    # Update top 5 with realtime prices
    try:
        top_tickers = [d['ticker'] for d in data[:5]]
        current_prices = fetch_realtime_data(top_tickers)
        for d in data[:5]:
            t = d['ticker']
            if t in current_prices:
                d['current_price'] = current_prices[t]['price']
                d['change'] = current_prices[t]['change']
    except:
        pass
        
    response = jsonify(data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/us/macro-analysis')
def get_macro_analysis():
    return jsonify(load_json('us_macro_analysis.json'))

@app.route('/api/us/sector-heatmap')
def get_sector_heatmap():
    return jsonify(load_json('sector_heatmap.json'))

@app.route('/api/us/options-flow')
def get_options_flow():
    return jsonify(load_json('options_flow.json'))

@app.route('/api/us/economic-calendar')
def get_calendar():
    return jsonify(load_json('economic_calendar.json'))

@app.route('/api/us/ai-summary/<ticker>')
def get_ai_summary(ticker):
    summaries = load_json('ai_stock_summaries.json')
    summary = summaries.get(ticker, "No summary available.")
    return jsonify({'ticker': ticker, 'summary': summary})

@app.route('/api/us/daily-report')
@app.route('/daily-report')
def get_daily_report():
    try:
        generator = USDailyReportGenerator(data_dir=DATA_DIR)
        return generator.run()
    except Exception as e:
        return f"<h1>Error generating report</h1><p>{str(e)}</p>", 500

@app.route('/api/us/realtime-prices')
def get_realtime_prices():
    tickers = request.args.get('tickers', 'SPY,QQQ,NVDA,AAPL,TSLA').split(',')
    try:
        return jsonify(fetch_realtime_data(tickers))
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
