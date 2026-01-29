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
# Robust path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    import us_market
    DATA_DIR = os.path.dirname(us_market.__file__)
except:
    DATA_DIR = os.path.join(BASE_DIR, 'us_market')

from us_market.daily_report_generator import USDailyReportGenerator

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'assets'),
            static_url_path='/assets')

print(f"DEBUG: BASE_DIR={BASE_DIR}")
print(f"DEBUG: DATA_DIR={DATA_DIR}")

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    data = {}
    print(f"DEBUG: Trying to load JSON from {path}")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"DEBUG: Successfully loaded JSON {filename}")
        except Exception as e:
            print(f"DEBUG: Error reading {filename}: {e}")
    else:
        print(f"DEBUG: JSON NOT FOUND at {path}")
    
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
    # Try multiple potential paths to be robust against different execution environments
    possible_paths = [
        os.path.join(DATA_DIR, filename),                      # Derived from package/file location
        os.path.join(os.getcwd(), 'us_market', filename),       # From root if run as 'python app.py'
        os.path.join(os.getcwd(), filename),                   # If run from inside 'us_market/'
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'us_market', filename)) # Relative to api/
    ]
    
    data = []
    path_to_use = None
    
    for path in possible_paths:
        print(f"DEBUG: Checking path: {path}")
        if os.path.exists(path):
            path_to_use = path
            print(f"DEBUG: Found file at {path}, size={os.path.getsize(path)}")
            # Even if size is small, we try to load it (removed > 100 check)
            break
            
    if path_to_use:
        # Try multiple encodings for Korean Windows compatibility
        for enc in ['utf-8-sig', 'utf-8', 'cp949']:
            try:
                with open(path_to_use, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    # Strip whitespace from field names
                    reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
                    data = []
                    for row in reader:
                        # Cleanup values and normalize field names
                        row = {k.strip() if k else k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                        
                        if 'composite_score' in row and 'score' not in row:
                            row['score'] = row['composite_score']
                        
                        # Ensure numeric types for sorting/display
                        try:
                            row['score'] = float(row.get('score', 0))
                            row['price'] = float(row.get('price', row.get('current_price', 0)))
                            row['change'] = float(row.get('change', 0))
                        except Exception as e:
                            print(f"DEBUG: Data conversion error for {row.get('ticker')}: {e}")
                            
                        data.append(row)
                        
                    if data:
                        print(f"DEBUG: Successfully loaded {len(data)} rows from {path_to_use}")
                        print(f"DEBUG: First row preview: {data[0]}")
                        break
            except Exception as e:
                print(f"DEBUG: Failed to read {path_to_use} with {enc}: {e}")
    else:
        print(f"DEBUG: Could not find a valid CSV file for {filename} in any searched location.")
    
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
                "swot_o": "자율주행 및 엣지 AI 시장 확대", "swot_t": "중국 수출 규제 및 경쟁 심화",
                "dcf_target": "$165.00", "dcf_bear": "$125.00", "dcf_bull": "$190.00"
            },
            {
                "rank": "02", "ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Automotive", 
                "composite_score": "91.2", "grade": "🌟 A급 (적극 매수)", "price": "258.45", "change": "3.1",
                "insight": "FSD v12 및 로보택시 기대감이 강력한 모멘텀을 형성하고 있으며, 비용 절감 노력이 마진을 방어 중입니다.",
                "risk": "전기차 시장의 경쟁 심화와 중국 시장 점유율 둔화 가능성.",
                "upside": "+25.5%", "mkt_cap": "$825B", "vol_ratio": "2.4x ↑", "rsi": "64.5",
                "swot_s": "자율주행 데이터 우위 및 브랜드 파워", "swot_w": "CEO 리스크 및 생산 효율화 과제",
                "swot_o": "옵티머스 로봇 및 에너지 저장 사업", "swot_t": "중국산 저가 전기차 공세",
                "dcf_target": "$320.00", "dcf_bear": "$210.00", "dcf_bull": "$410.00"
            },
            {
                "rank": "03", "ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", 
                "composite_score": "88.5", "grade": "🌟 A급 (적극 매수)", "price": "228.12", "change": "1.2",
                "insight": "애플 인텔리전스(AI)가 차기 아이폰 교체 수요의 핵심 동력으로 작용할 것으로 분석됩니다.",
                "risk": "앱스토어 반독점 규제 및 중국 내 판매 둔화 리스크.",
                "upside": "+12.1%", "mkt_cap": "$3.4T", "vol_ratio": "1.2x ↑", "rsi": "55.4",
                "swot_s": "충성도 높은 생태계 및 강력한 현금흐름", "swot_w": "하드웨어 혁신 속도 둔화",
                "swot_o": "AI 기반 서비스 부문 매출 확대", "swot_t": "글로벌 규제 당국의 반독점 조사",
                "dcf_target": "$255.00", "dcf_bear": "$205.00", "dcf_bull": "$285.00"
            },
            {
                "rank": "04", "ticker": "MSFT", "name": "Microsoft Corp", "sector": "Software", 
                "composite_score": "82.5", "grade": "🌟 A급 (적극 매수)", "price": "425.30", "change": "0.9",
                "insight": "Azure 클라우드와 OpenAI 파트너십을 통한 기업용 AI 시장 지배력이 수익성 개선을 견인하고 있습니다.",
                "risk": "성장 둔화 우려 및 클라우드 부문 마진 압박 가능성.",
                "upside": "+17.5%", "mkt_cap": "$3.1T", "vol_ratio": "1.1x", "rsi": "52.3",
                "swot_s": "클라우드 및 기업용 소프트웨어 독점력", "swot_w": "높은 밸류에이션 부담",
                "swot_o": "생성형 AI 서비스의 전사적 통합", "swot_t": "AWS와 구글의 클라우드 추격",
                "dcf_target": "$505.00", "dcf_bear": "$410.00", "dcf_bull": "$580.00"
            },
            {
                "rank": "05", "ticker": "AMZN", "name": "Amazon.com", "sector": "Commerce", 
                "composite_score": "78.5", "grade": "📈 B급 (매수 고려)", "price": "188.30", "change": "0.5",
                "insight": "물류 효율화와 AWS 수익성 개선이 성장의 핵심입니다. 마진율이 점진적으로 상승하고 있습니다.",
                "risk": "소비 심리 위축 및 반독점 규제 강화.",
                "upside": "+22.1%", "mkt_cap": "$1.9T", "vol_ratio": "1.5x", "rsi": "58.7",
                "swot_s": "이커머스 압도적 점유율 및 AWS", "swot_w": "인건비 등 비용 관리 부담",
                "swot_o": "광업 부문 고성장 및 AI 클라우드", "swot_t": "중국계 쇼핑앱과의 경쟁 심화",
                "dcf_target": "$230.00", "dcf_bear": "$175.00", "dcf_bull": "$275.00"
            },
            {
                "rank": "06", "ticker": "META", "name": "Meta Platforms", "sector": "Technology", 
                "composite_score": "77.2", "grade": "📈 B급 (매수 고려)", "price": "585.20", "change": "1.4",
                "insight": "광고 매출 회복세가 뚜렷하며, Llama AI 모델 기반 서비스 최적화가 긍정적입니다.",
                "risk": "리얼리티 랩스의 막대한 적자 및 규제 리스크.",
                "upside": "+16.2%", "mkt_cap": "$1.4T", "vol_ratio": "1.8x", "rsi": "61.2",
                "swot_s": "페이스북/인스타그램 거대한 사용자 층", "swot_w": "메타버스 사업부문의 지속적 손실",
                "swot_o": "AI 타겟팅 광고를 통한 수익성 제고", "swot_t": "틱톡과의 사용자 점유율 경쟁",
                "dcf_target": "$680.00", "dcf_bear": "$550.00", "dcf_bull": "$780.00"
            },
            {
                "rank": "07", "ticker": "GOOGL", "name": "Alphabet Inc", "sector": "Technology", 
                "composite_score": "76.5", "grade": "📈 B급 (매수 고려)", "price": "165.20", "change": "0.0",
                "insight": "검색 광고 시장의 견고함과 구글 클라우드 흑자 전환이 긍정적이나 AI 검색 경쟁이 변수입니다.",
                "risk": "반독점 소송 리스크 및 AI 검색 시장의 경쟁 심화.",
                "upside": "+24.2%", "mkt_cap": "$2.1T", "vol_ratio": "0.9x", "rsi": "49.5",
                "swot_s": "글로벌 검색 시장 점유율 1위", "swot_w": "AI 대응 속도에 대한 시장 우려",
                "swot_o": "유튜브 쇼츠 수익화 및 제미나이 AI", "swot_t": "오픈AI 등 생성형 검색의 침공",
                "dcf_target": "$205.00", "dcf_bear": "$160.00", "dcf_bull": "$245.00"
            },
            {
                "rank": "08", "ticker": "AVGO", "name": "Broadcom Inc", "sector": "Semiconductors", 
                "composite_score": "75.8", "grade": "📈 B급 (매수 고려)", "price": "172.50", "change": "2.1",
                "insight": "커스텀 AI 가속기 및 네트워킹 장비 수요가 폭발적입니다. VMware 인수를 통한 소프트웨어 성장도 기대됩니다.",
                "risk": "하이엔드 네트워킹 시장의 경쟁 증가.",
                "upside": "+21.7%", "mkt_cap": "$800B", "vol_ratio": "2.1x", "rsi": "67.8",
                "swot_s": "네트워킹 칩 및 무선 통신 기술력", "swot_w": "VMware 통합 과정의 불확실성",
                "swot_o": "빅테크향 커스텀 AI 가속기 시장 확대", "swot_t": "반도체 사이클의 하강 가능성",
                "dcf_target": "$210.00", "dcf_bear": "$165.00", "dcf_bull": "$250.00"
            },
            {
                "rank": "09", "ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Semiconductors", 
                "composite_score": "74.2", "grade": "📈 B급 (매수 고려)", "price": "155.10", "change": "-2.3",
                "insight": "MI300 AI 가속기 출시를 통해 시장 점유율을 확대 중입니다. PC 및 데이터센터 수요 회복 수혜가 예상됩니다.",
                "risk": "NVIDIA와의 시장 점유율 경쟁 및 마진 압박.",
                "upside": "+35.4%", "mkt_cap": "$250B", "vol_ratio": "1.4x", "rsi": "45.2",
                "swot_s": "CPU 및 GPU 라인업의 강력한 경쟁력", "swot_w": "엔비디아 대비 낮은 AI 생태계 영향력",
                "swot_o": "AI 가속기 시장의 2순위 공급자 지위", "swot_t": "시장 성장이 공급 증가를 못 따라갈 리스크",
                "dcf_target": "$210.00", "dcf_bear": "$145.00", "dcf_bull": "$280.00"
            },
            {
                "rank": "10", "ticker": "COST", "name": "Costco Wholesale", "sector": "Retail", 
                "composite_score": "73.5", "grade": "📊 C급 (관망)", "price": "912.45", "change": "0.8",
                "insight": "멤버십 기반의 강력한 고객 충성도와 이커머스 성장이 안정적인 수익을 창출하고 있습니다.",
                "risk": "높은 PER 밸류에이션 수준 및 경쟁 심화.",
                "upside": "+10.7%", "mkt_cap": "$400B", "vol_ratio": "0.8x", "rsi": "51.1",
                "swot_s": "멤버십 모델을 통한 현금 흐름 안정성", "swot_w": "저성장 산업군의 특성",
                "swot_o": "글로벌 매장 확대 및 온라인 채널 강화", "swot_t": "월마트 등 대형 할인점의 멤버십 강화",
                "dcf_target": "$1010.00", "dcf_bear": "$880.00", "dcf_bull": "$1150.00"
            }
        ]
    # Provide default ETF flow data if missing
    if not data and filename == 'us_etf_flows.csv':
        return [
            {"ticker": "SPY", "name": "SPDR S&P 500", "flow_score": "82.5", "price_change_20d": "2.1"},
            {"ticker": "QQQ", "name": "Invesco QQQ", "flow_score": "78.4", "price_change_20d": "3.2"},
            {"ticker": "XLK", "name": "Technology", "flow_score": "91.2", "price_change_20d": "5.5"},
            {"ticker": "XLU", "name": "Utilities", "flow_score": "32.5", "price_change_20d": "-2.1"}
        ]
    return data or []

def fetch_realtime_data(tickers):
    """Manual fetch for Yahoo Finance v8 (Stable for server-side)"""
    prices = {}
    print(f"DEBUG: Fetching prices for {len(tickers)} tickers")
    
    # Limit to top 10 for speed to avoid timeouts (increased from 5)
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
        
    response = jsonify(data[:10])
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/us/macro-analysis')
def get_macro_analysis():
    return jsonify(load_json('us_macro_analysis.json'))

@app.route('/api/us/sector-heatmap')
def get_sector_heatmap():
    return jsonify(load_json('sector_heatmap.json'))

@app.route('/api/us/etf-flows')
def get_etf_flows():
    return jsonify(load_csv('us_etf_flows.csv'))

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
    report_path = os.path.join(DATA_DIR, 'us_market_morning_report.html')
    
    # 1. First, check if the pre-generated file exists
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"DEBUG: Error reading existing report: {e}")

    # 2. Fallback to live generation if file doesn't exist or failed to read
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

@app.route('/api/debug')
def debug_server():
    debug_info = {
        "BASE_DIR": BASE_DIR,
        "DATA_DIR": DATA_DIR,
        "CWD": os.getcwd(),
        "sys.path": sys.path,
        "files_in_data_dir": os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else "DIR_NOT_FOUND",
        "csv_exists": os.path.exists(os.path.join(DATA_DIR, 'smart_money_picks_v2.csv'))
    }
    return jsonify(debug_info)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
