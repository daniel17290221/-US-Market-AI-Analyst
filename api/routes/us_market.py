from flask import Blueprint, jsonify, request, make_response, send_file
import os
import json
import requests
from datetime import datetime
try:
    from utils import (
        DATA_DIR, BASE_DIR, major_us_analysis, 
        load_json, load_csv, fetch_realtime_data, fetch_dynamic_ai_analysis,
        logger
    )
except ImportError:
    from ..utils import (
        DATA_DIR, BASE_DIR, major_us_analysis, 
        load_json, load_csv, fetch_realtime_data, fetch_dynamic_ai_analysis,
        logger
    )

us_market_bp = Blueprint('us_market', __name__)

@us_market_bp.route('/api/us/macro-analysis', strict_slashes=False)
def get_macro_analysis():
    return jsonify(load_json('us_macro_analysis.json'))

@us_market_bp.route('/api/us/sector-heatmap', strict_slashes=False)
def get_sector_heatmap():
    return jsonify(load_json('sector_heatmap.json'))

@us_market_bp.route('/api/us/etf-flows', strict_slashes=False)
def get_etf_flows():
    return jsonify(load_csv('us_etf_flows.csv'))

@us_market_bp.route('/api/us/options-flow', strict_slashes=False)
def get_options_flow():
    return jsonify(load_json('options_flow.json'))

@us_market_bp.route('/api/us/economic-calendar', strict_slashes=False)
def get_calendar():
    return jsonify(load_json('economic_calendar.json'))

@us_market_bp.route('/api/us/ai-summary/<ticker>', strict_slashes=False)
def get_ai_summary(ticker):
    summaries = load_json('ai_stock_summaries.json')
    summary = summaries.get(ticker, "No summary available.")
    return jsonify({'ticker': ticker, 'summary': summary})

@us_market_bp.route('/api/us/realtime-prices', strict_slashes=False)
def get_realtime_prices():
    tickers = request.args.get('tickers', 'SPY,QQQ,NVDA,AAPL,TSLA').split(',')
    try:
        return jsonify(fetch_realtime_data(tickers))
    except Exception as e:
        return jsonify({'error': str(e)})

@us_market_bp.route('/api/us/smart-money', strict_slashes=False)
def get_smart_money():
    data = load_csv('smart_money_picks_v2.csv')
    if not data: return jsonify([])

    # Price update
    try:
        top_tickers = [d['ticker'] for d in data[:15]]
        current_prices = fetch_realtime_data(top_tickers)
        for d in data:
            t = d.get('ticker', '').strip().upper()
            if t in current_prices:
                d['price'] = current_prices[t]['price']
                d['change'] = current_prices[t]['change']
    except Exception as e:
        logger.error(f"US Price update error: {e}")

    precomputed_ai = load_json('us_ai_analysis.json')
    dynamic_results = precomputed_ai.copy()
    
    # Identify stocks needing dynamic analysis (Normalized tickers)
    stocks_to_analyze = []
    for d in data[:15]:
        ticker = str(d.get('ticker', '')).strip().upper()
        if not ticker: continue
        if ticker not in major_us_analysis and ticker not in dynamic_results:
            stocks_to_analyze.append({'symbol': ticker, 'name': d.get('name', ticker)})
    
    # Fetch dynamic AI analysis if needed
    if stocks_to_analyze:
        try:
            new_analyses = fetch_dynamic_ai_analysis(stocks_to_analyze)
            dynamic_results.update(new_analyses)
        except Exception as e:
            logger.error(f"Dynamic AI analysis error: {e}")

    enriched = []
    for i, d in enumerate(data[:15]):
        ticker = str(d.get('ticker', d.get('symbol', ''))).strip().upper()
        if not ticker: continue
        
        details = major_us_analysis.get(ticker) or dynamic_results.get(ticker)
        
        if not details:
            details = {
                "insight": "실시간 데이터 분석 중입니다.", 
                "risk": "데이터 확인 필요", 
                "upside": "-", "mkt_cap": "-", "vol_ratio": "-", "rsi": "-", 
                "swot_s": "-", "swot_w": "-", "swot_o": "-", "swot_t": "-", 
                "dcf_target": str(d.get('price', '0')), "dcf_bear": "-", "dcf_bull": "-"
            }
        
        enriched.append({
            **d, **details,
            "rank": str(i+1).zfill(2),
            "signal": "매수" if i < 8 else "중립"
        })

    response = jsonify(enriched)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@us_market_bp.route('/api/us/daily-report', strict_slashes=False)
@us_market_bp.route('/daily-report', strict_slashes=False)
def get_daily_report():
    # Primary: GitHub Pages URL — always updated by 'Deploy to MAIN Domain Repository' step
    # This is the most reliable source since it's explicitly cloned and pushed each run
    github_pages_url = "https://raw.githubusercontent.com/daniel17290221/daniel17290221.github.io/main/report_us.html"
    
    # Secondary: Raw source repo (may lag if commit was skipped due to .gitignore)
    github_raw_repo = "https://raw.githubusercontent.com/daniel17290221/-US-Market-AI-Analyst/main/us_market/us_market_morning_report.html"
    
    # Tertiary: Custom Domain
    domain_url = "https://land.vibe-coding-lab.com/report_us.html"
    
    urls = [github_pages_url, github_raw_repo, domain_url]
    for url in urls:
        try:
            params = {"t": int(datetime.now().timestamp())} # Cache busting
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200 and len(resp.text) > 1000:
                response = make_response(resp.text)
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                return response
        except: continue

    # Final Fallback: Local file (packaged with deployment)
    paths = [
        os.path.join(DATA_DIR, 'us_market_morning_report.html'),
        os.path.join(BASE_DIR, 'us_market', 'us_market_morning_report.html')
    ]
    for p in paths:
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            response = make_response(send_file(p, mimetype='text/html'))
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            return response

    return "Report not found", 404
