from flask import Blueprint, jsonify, request, make_response, send_file
import os
import json
import requests
import concurrent.futures
from datetime import datetime
try:
    from utils import (
        BASE_DIR, KR_DATA_DIR, MAJOR_ANALYSIS_KR, 
        fetch_naver_movers, fetch_realtime_data, fetch_dynamic_ai_analysis, fetch_google_news_rss,
        logger
    )
except ImportError:
    from ..utils import (
        BASE_DIR, KR_DATA_DIR, MAJOR_ANALYSIS_KR, 
        fetch_naver_movers, fetch_realtime_data, fetch_dynamic_ai_analysis, fetch_google_news_rss,
        logger
    )

kr_market_bp = Blueprint('kr_market', __name__)

@kr_market_bp.route('/api/kr/debug-price', strict_slashes=False)
def debug_kr_price():
    possible_paths = [
        os.path.join(KR_DATA_DIR, 'kr_market', 'kr_daily_data.json'),
        os.path.join(KR_DATA_DIR, 'kr_daily_data.json'),
        os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market', 'kr_daily_data.json'),
        os.path.join(BASE_DIR, 'kr_market', 'kr_daily_data.json')
    ]
    found_path = None
    for p in possible_paths:
        if p and os.path.exists(p):
            found_path = p
            break
    
    data = {}
    if not found_path:
        try:
            github_raw_url = "https://raw.githubusercontent.com/daniel17290221/-US-Market-AI-Analyst/main/KR_Market_Analyst/kr_market/kr_daily_data.json"
            resp = requests.get(github_raw_url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                found_path = "github_raw"
            else:
                return jsonify({"error": "JSON not found", "searched": possible_paths})
        except Exception as e:
            return jsonify({"error": f"JSON not found, GitHub failed: {e}", "searched": possible_paths})
    else:
        with open(found_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    leaders = data.get('leaders_kospi', [])
    return jsonify({
        "found_path": found_path,
        "date": data.get('date'),
        "leaders_count": len(leaders),
        "sample": leaders[:3]
    })

@kr_market_bp.route('/api/kr/market-data', strict_slashes=False)
def get_kr_market_data():
    possible_paths = [
        os.path.join(KR_DATA_DIR, 'kr_market', 'kr_daily_data.json'),
        os.path.join(KR_DATA_DIR, 'kr_daily_data.json'),
        os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market', 'kr_daily_data.json'),
        os.path.join(BASE_DIR, 'kr_market', 'kr_daily_data.json')
    ]
    
    kr_data_path = None
    latest_time = 0
    for p in possible_paths:
        if p and os.path.exists(p):
            mtime = os.path.getmtime(p)
            if mtime > latest_time:
                latest_time = mtime
                kr_data_path = p
    
    logger.info(f"KR Market Data Path Selected: {kr_data_path}")
    
    kr_data = {}
    if kr_data_path:
        try:
            with open(kr_data_path, 'r', encoding='utf-8') as f:
                kr_data = json.load(f)
        except Exception as e:
            logger.error(f"KR Data Load Error: {e}")
    else:
        logger.warning("No local KR Data Path found. Falling back to GitHub.")
        try:
            github_raw_url = "https://raw.githubusercontent.com/daniel17290221/-US-Market-AI-Analyst/main/KR_Market_Analyst/kr_market/kr_daily_data.json"
            resp = requests.get(github_raw_url, timeout=8)
            if resp.status_code == 200:
                kr_data = resp.json()
        except Exception as e:
            logger.error(f"GitHub fallback error: {e}")
    
    leaders_kospi = kr_data.get('leaders_kospi', [])
    leaders_kosdaq = kr_data.get('leaders_kosdaq', [])
    gainers = kr_data.get('gainers', [])
    volume = kr_data.get('volume', [])
    precomputed_ai = kr_data.get('ai_analysis', {})

    logger.info(f"KR Data Summary: KOSPI={len(leaders_kospi)}, KOSDAQ={len(leaders_kosdaq)}, Gainers={len(gainers)}, Volume={len(volume)}")
    
    if not leaders_kospi and not leaders_kosdaq:
        logger.info("Triggering Naver Live Fetch Fallback...")
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                f1 = executor.submit(fetch_naver_movers, 'rise', 0)
                f2 = executor.submit(fetch_naver_movers, 'rise', 1)
                f3 = executor.submit(fetch_naver_movers, 'volume', 0)
                f4 = executor.submit(fetch_naver_movers, 'volume', 1)
                f5 = executor.submit(fetch_naver_movers, 'cap', 0)
                f6 = executor.submit(fetch_naver_movers, 'cap', 1)
                g_kospi = f1.result() or []
                g_kosdaq = f2.result() or []
                v_kospi = f3.result() or []
                v_kosdaq = f4.result() or []
                l_kospi = f5.result() or []
                l_kosdaq = f6.result() or []
            gainers = (g_kospi[:10] + g_kosdaq[:10]) 
            volume = (v_kospi[:10] + v_kosdaq[:10])
            leaders_kospi = l_kospi[:10]
            leaders_kosdaq = l_kosdaq[:10]
        except Exception as e:
            logger.error(f"Live fetch error: {e}")

    # Price updates (Simplified for Vercel)
    if not os.environ.get('VERCEL'):
        try:
             all_tickers = list(set([f"{s['symbol']}.KS" for s in leaders_kospi] + [f"{s['symbol']}.KQ" for s in leaders_kosdaq]))
             current_prices = fetch_realtime_data(all_tickers)
             # Map back logic... (Abbreviated here for route clarity, you can implement fully)
        except: pass

    dynamic_results = precomputed_ai.copy()
    
    def enrich_list(stock_list):
        enriched = []
        if not stock_list: return []
        for i, s in enumerate(stock_list):
            try:
                symbol = s.get('symbol', '000000')
                details = MAJOR_ANALYSIS_KR.get(symbol) or dynamic_results.get(symbol)
                if not details:
                    details = {"insight": "분석 정보 준비 중입니다.", "risk": "-", "upside": "-", "mkt_cap": "-", "vol_ratio": "-", "rsi": "-", "swot_s": "-", "swot_w": "-", "swot_o": "-", "swot_t": "-", "dcf_target": "-", "dcf_bear": "-", "dcf_bull": "-"}
                
                price_clean = s.get('price', '--') or '--'
                try:
                    change_raw = str(s.get('change', '0')).replace('%', '').replace(',', '').strip()
                    change_clean = round(float(change_raw), 2)
                except: change_clean = 0.0

                enriched.append({
                    "rank": str(i+1).zfill(2),
                    "ticker": s.get('name', 'N/A'),
                    "symbol": symbol,
                    "name": s.get('name', 'N/A'),
                    "sector": s.get('market', 'KOSPI'),
                    "score": round(90.0 - (i * 0.5), 1),
                    "signal": "매수",
                    **details,
                    "price": price_clean,
                    "change": change_clean,
                })
            except Exception as e:
                logger.error(f"Error enriching stock {s}: {e}")
        return enriched

    try:
        response_data = {
            "date": kr_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')),
            "leaders_kospi": enrich_list(leaders_kospi),
            "leaders_kosdaq": enrich_list(leaders_kosdaq),
            "gainers": enrich_list(gainers),
            "volume": enrich_list(volume),
            "sector_heatmap": kr_data.get('sector_heatmap', []),
            "ipo_news": kr_data.get('ipo_news', []),
            "market_news": kr_data.get('market_news', [])
        }
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error structuring KR response: {e}")
        return jsonify({"error": "Data structure failed", "details": str(e)}), 500

@kr_market_bp.route('/api/kr/news', strict_slashes=False)
@kr_market_bp.route('/kr/news', strict_slashes=False)
def get_kr_news():
    return jsonify(fetch_google_news_rss("국내+증시+시황+마감+브리핑"))

@kr_market_bp.route('/api/kr/ipo', strict_slashes=False)
@kr_market_bp.route('/kr/ipo', strict_slashes=False)
def get_kr_ipo():
    try:
        kr_data_path = os.path.join(BASE_DIR, 'KR_Market_Analyst/kr_market/kr_daily_data.json')
        if os.path.exists(kr_data_path):
            with open(kr_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data.get('ipo_news', []))
        return jsonify(fetch_google_news_rss("공모주+청약+일정+상장"))
    except: return jsonify([])

@kr_market_bp.route('/api/kr/report', strict_slashes=False)
@kr_market_bp.route('/api/kr/daily-report', strict_slashes=False)
@kr_market_bp.route('/kr/daily-report', strict_slashes=False)
def get_kr_daily_report():
    # Primary: GitHub Pages URL — always updated by 'Deploy to MAIN Domain Repository' step
    github_pages_url = "https://raw.githubusercontent.com/daniel17290221/daniel17290221.github.io/main/report_kr.html"
    
    # Secondary: Raw source repo
    github_raw_repo = "https://raw.githubusercontent.com/daniel17290221/-US-Market-AI-Analyst/main/KR_Market_Analyst/kr_market/kr_market_daily_report.html"
    
    # Tertiary: Custom Domain
    domain_url = "https://land.vibe-coding-lab.com/report_kr.html"
    
    urls = [github_pages_url, github_raw_repo, domain_url]
    for url in urls:
        try:
            params = {"t": int(datetime.now().timestamp())} # Cache busting
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200 and len(resp.text) > 1000:
                response = make_response(resp.text)
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                return response
        except: continue

    # Final Fallback: Local file
    paths = [
        os.path.join(KR_DATA_DIR, 'kr_market', 'kr_market_daily_report.html'),
        os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market', 'kr_market_daily_report.html')
    ]
    for p in paths:
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            resp = make_response(send_file(p, mimetype='text/html'))
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            resp.headers['Content-Type'] = 'text/html; charset=utf-8'
            return resp

    return "Report not found", 404
