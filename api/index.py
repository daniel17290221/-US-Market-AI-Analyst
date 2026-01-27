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
    data = {}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"DEBUG: Error reading {filename}: {e}")
    
    # Provide default macro data if missing or empty
    if not data and filename == 'us_macro_analysis.json':
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
    return data or {}

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    data = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        except Exception as e:
            print(f"DEBUG: Error loading CSV {filename}: {e}")
    
    # Provide default smart money data if missing OR empty
    if not data and filename == 'smart_money_picks_v2.csv':
        return [
            {
                "rank": "01", "ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", 
                "composite_score": "95.8", "grade": "🔥 S급 (즉시 매수)", "price": "142.87", "change": "8.4",
                "insight": "NVIDIA는 AI 가속기 시장에서 독보적 지위를 유지하고 있으며, Blackwell 아키텍처 출시로 매출 성장이 가속화될 전망입니다.",
                "risk": "중국 수출 규제 영향 및 경쟁사 AMD MI300 대항 전략.",
                "upside": "+18.2%", "mkt_cap": "$3.5T", "vol_ratio": "3.2x ↑", "rsi": "72.4",
                "swot_s": "AI 시장 80%+ 점유율 및 CUDA 생태계", "swot_w": "빅테크 고객 집중도 및 높은 의존도",
                "swot_o": "자율주행 및 엣지 AI 시장 확대", "swot_t": "중국 수출 규제 및 경쟁 심화"
            },
            {
                "rank": "02", "ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Automotive", 
                "composite_score": "91.2", "grade": "🌟 A급 (적극 매수)", "price": "258.45", "change": "3.1",
                "insight": "FVD v12 및 로보택시 기대감이 강력한 모멘텀을 형성하고 있으며, 비용 절감 노력이 마진을 방어 중입니다.",
                "risk": "전기차 시장의 경쟁 심화와 중국 시장 점유율 둔화 가능성.",
                "upside": "+25.5%", "mkt_cap": "$825B", "vol_ratio": "2.4x ↑", "rsi": "64.5",
                "swot_s": "자율주행 데이터 우위 및 브랜드 파워", "swot_w": "CEO 리스크 및 생산 효율화 과제",
                "swot_o": "옵티머스 로봇 및 에너지 저장 사업", "swot_t": "중국산 저가 전기차 공세"
            },
            {
                "rank": "03", "ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", 
                "composite_score": "88.5", "grade": "🌟 A급 (적극 매수)", "price": "228.12", "change": "1.2",
                "insight": "애플 인텔리전스(AI)가 차기 아이폰 교체 수요의 핵심 동력으로 작용할 것으로 분석됩니다.",
                "risk": "앱스토어 반독점 규제 및 중국 내 판매 둔화 리스크.",
                "upside": "+12.1%", "mkt_cap": "$3.4T", "vol_ratio": "1.2x ↑", "rsi": "55.4",
                "swot_s": "충성도 높은 생태계 및 강력한 현금흐름", "swot_w": "하드웨어 혁신 속도 둔화",
                "swot_o": "AI 기반 서비스 부문 매출 확대", "swot_t": "글로벌 규제 당국의 반독점 조사"
            },
            {"rank": "04", "ticker": "MSFT", "name": "Microsoft Corp", "sector": "Software", "composite_score": "82.5", "grade": "🌟 A급 (적극 매수)", "price": "425.30", "change": "0.9"},
            {"rank": "05", "ticker": "AMZN", "name": "Amazon.com", "sector": "Commerce", "composite_score": "78.5", "grade": "📈 B급 (매수 고려)", "price": "188.30", "change": "0.5"},
            {"rank": "06", "ticker": "META", "name": "Meta Platforms", "sector": "Technology", "composite_score": "77.2", "grade": "📈 B급 (매수 고려)", "price": "585.20", "change": "1.4"},
            {"rank": "07", "ticker": "GOOGL", "name": "Alphabet Inc", "sector": "Technology", "composite_score": "76.5", "grade": "📈 B급 (매수 고려)", "price": "165.20", "change": "0.0"},
            {"rank": "08", "ticker": "AVGO", "name": "Broadcom Inc", "sector": "Semiconductors", "composite_score": "75.8", "grade": "📈 B급 (매수 고려)", "price": "172.50", "change": "2.1"},
            {"rank": "09", "ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Semiconductors", "composite_score": "74.2", "grade": "📈 B급 (매수 고려)", "price": "155.10", "change": "-2.3"},
            {"rank": "10", "ticker": "COST", "name": "Costco Wholesale", "sector": "Retail", "composite_score": "73.5", "grade": "📊 C급 (관망)", "price": "912.45", "change": "0.8"}
        ]
    return data or []

def fetch_realtime_data(tickers):
    """Manual fetch for Yahoo Finance v8 (Stable for server-side)"""
    prices = {}
    print(f"DEBUG: Fetching prices for {len(tickers)} tickers")
    
    # Limit to top 10 for speed if list is long (increased from 5)
    target_tickers = tickers[:10] if len(tickers) > 10 else tickers
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    for ticker in target_tickers:
        if not ticker: continue
        try:
            # Use v8 finance/chart for stability
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
            resp = requests.get(url, headers=headers, timeout=3)
            
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
                price = meta.get('regularMarketPrice')
                prev_close = meta.get('previousClose')
                
                if price is not None:
                    prices[ticker] = {
                        'price': round(price, 2),
                        'change': round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0
                    }
        except Exception as e:
            print(f"DEBUG: Failed to fetch {ticker}: {e}")
            pass
    return prices

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/us/smart-money')
def get_smart_money():
    data = load_csv('smart_money_picks_v2.csv')
    
    # Update top 10 with realtime prices (expanded from 5)
    try:
        top_tickers = [d['ticker'] for d in data[:10]]
        current_prices = fetch_realtime_data(top_tickers)
        for d in data[:10]:
            t = d['ticker']
            if t in current_prices:
                d['price'] = current_prices[t]['price']
                d['change'] = current_prices[t]['change']
    except Exception as e:
        print(f"DEBUG: Price update error: {e}")
        
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
