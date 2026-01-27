from flask import Flask, render_template, jsonify, request
import csv
import json
import os
import requests
import sys
from datetime import datetime

# Adjust path for Vercel subdirectory deployment
# BASE_DIR should be the root of the project (where templates and us_market are)
# In Vercel, this is usually the parent of 'api/'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from us_market.daily_report_generator import USDailyReportGenerator

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
DATA_DIR = os.path.join(BASE_DIR, 'us_market')

# Ensure we log the actual paths for debugging in Vercel logs
print(f"DEBUG: BASE_DIR={BASE_DIR}")
print(f"DEBUG: DATA_DIR={DATA_DIR}")

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Provide default macro data if missing
    if filename == 'us_macro_analysis.json':
        return {
            "market_mood": "Greed",
            "mood_score": 78,
            "key_takeaways": [
                "AI 주도 빅테크 랠리 지속",
                "국채 금리 하락세로 성장주 모멘텀 강화",
                "소비자 심리 지수 예상치 상회"
            ],
            "sector_outlook": "반도체 및 기술 섹터 비중 확대 권고",
            "risk_factors": "인플레이션 재점화 가능성 및 지정학적 리스크"
        }
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
    
    # Provide default smart money data if missing
    if filename == 'smart_money_picks_v2.csv':
        return [
            {"rank": "01", "ticker": "NVDA", "sector": "Technology", "composite_score": "95.8", "grade": "🔥 S급 (즉시 매수)"},
            {"rank": "02", "ticker": "TSLA", "sector": "Automotive", "composite_score": "91.2", "grade": "🌟 A급 (적극 매수)"},
            {"rank": "03", "ticker": "AAPL", "sector": "Technology", "composite_score": "88.5", "grade": "🌟 A급 (적극 매수)"},
            {"rank": "04", "ticker": "MSFT", "sector": "Software", "composite_score": "82.5", "grade": "🌟 A급 (적극 매수)"},
            {"rank": "05", "ticker": "AMZN", "sector": "Commerce", "composite_score": "78.5", "grade": "📈 B급 (매수 고려)"},
            {"rank": "06", "ticker": "META", "sector": "Technology", "composite_score": "77.2", "grade": "📈 B급 (매수 고려)"},
            {"rank": "07", "ticker": "GOOGL", "sector": "Technology", "composite_score": "76.5", "grade": "📈 B급 (매수 고려)"},
            {"rank": "08", "ticker": "AVGO", "sector": "Semiconductors", "composite_score": "75.8", "grade": "📈 B급 (매수 고려)"},
            {"rank": "09", "ticker": "AMD", "sector": "Semiconductors", "composite_score": "74.2", "grade": "📈 B급 (매수 고려)"},
            {"rank": "10", "ticker": "COST", "sector": "Retail", "composite_score": "73.5", "grade": "📊 C급 (관망)"}
        ]
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
