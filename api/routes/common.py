from flask import Blueprint, jsonify, request, make_response
import os
import json
import requests
from datetime import datetime
from utils import (
    DATA_DIR, BASE_DIR, AI_KEY, get_exchange_rate, portfolio_rate_limit,
    fetch_yahoo_history, logger
)

common_bp = Blueprint('common', __name__)

@common_bp.route('/ads.txt', strict_slashes=False)
def serve_ads_txt():
    content = "google.com, pub-4995156883730033, DIRECT, f08c47fec0942fa0"
    return make_response(content, 200, {'Content-Type': 'text/plain'})

@common_bp.route('/api/cron/update', strict_slashes=False)
def cron_update():
    results = {}
    try:
        from us_market.daily_report_generator import USDailyReportGenerator
        us_gen = USDailyReportGenerator(data_dir=DATA_DIR)
        us_gen.run()
        results["us"] = "success"
    except Exception as e:
        results["us"] = f"error: {str(e)}"

    try:
        kr_base = os.path.join(BASE_DIR, 'KR_Market_Analyst')
        kr_market_dir = os.path.join(kr_base, 'kr_market')
        from KR_Market_Analyst.kr_market.kr_data_manager import KRDataManager
        from KR_Market_Analyst.kr_market.kr_report_generator import KRDailyReportGenerator
        data_manager = KRDataManager(output_dir=kr_market_dir)
        data_manager.collect_all()
        report_gen = KRDailyReportGenerator(data_dir=kr_market_dir)
        report_gen.run()
        results["kr"] = "success"
    except Exception as e:
        results["kr"] = f"error: {str(e)}"

    status_code = 200 if all(v == "success" for v in results.values()) else 207
    return jsonify({"status": "completed", "details": results}), status_code

@common_bp.route('/api/chart-data', strict_slashes=False)
def get_universal_chart_data():
    symbol = request.args.get('symbol', '005930')
    market = request.args.get('market', 'KR')
    if not symbol: return jsonify([])
    ticker_sym = symbol.upper() if market.upper() == 'US' else f"{symbol}.KS"
    try:
        data = fetch_yahoo_history(ticker_sym)
        if not data and market.upper() == 'KR':
            data = fetch_yahoo_history(f"{symbol}.KQ")
        return jsonify(data)
    except Exception as e:
        logger.error(f"Chart data error for {symbol}: {e}")
        return jsonify([])

@common_bp.route('/api/generate-portfolio', methods=['POST'], strict_slashes=False)
def generate_portfolio():
    client_ip = request.remote_addr
    req_json = request.get_json(silent=True) or {}
    dev_mode = req_json.get('dev_mode', False) or request.args.get('dev_mode') == 'vibecoding'
    is_local = client_ip in ['127.0.0.1', 'localhost', '::1']
    
    if not dev_mode and not is_local:
        today = datetime.now().strftime("%Y-%m-%d")
        if client_ip not in portfolio_rate_limit:
            portfolio_rate_limit[client_ip] = {'date': today, 'count': 0}
        if portfolio_rate_limit[client_ip]['date'] != today:
            portfolio_rate_limit[client_ip] = {'date': today, 'count': 0}
        if portfolio_rate_limit[client_ip]['count'] >= 3:
            return jsonify({"error": "Rate limit exceeded", "message": "하루 3회 제한 도달"}), 429
        portfolio_rate_limit[client_ip]['count'] += 1

    theme = req_json.get('theme', '배당 투자')
    risk = req_json.get('risk', '중립')
    amount_krw = int(str(req_json.get('amount', '100000000')).replace(',', '').replace('원', ''))
    strategy = req_json.get('strategy', '배당 수익 극대화')
    market = req_json.get('market', 'US')
    etf_mode = req_json.get('etf_mode', False)
    
    exchange_rate = get_exchange_rate()
    
    prompt = f"금액: {amount_krw:,} KRW, 테마: {theme}, 성향: {risk}, 전략: {strategy}, 시장: {market}, ETF전용: {etf_mode}. 포트폴리오 5-7개 종목 구성. JSON format only."
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={AI_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code != 200: return jsonify({"error": "AI API Error"}), 500
        
        result = json.loads(resp.json()['candidates'][0]['content']['parts'][0]['text'].strip())
        
        total_dividend_krw = 0
        portfolio_list = []
        for item in result.get('portfolio', []):
            weight = float(str(item.get('weight', 0)).replace('%','')) / 100 if '%' in str(item.get('weight', 0)) else float(item.get('weight', 0))
            if weight > 1: weight /= 100
            
            invest_krw = amount_krw * weight
            currency = item.get('currency', 'USD').upper()
            price_raw = float(item.get('price', 0))
            yield_pct = float(item.get('yield_pct', 0)) / 100
            
            if currency == 'USD':
                display_price = f"${price_raw:,.2f}"
                annual_div_krw = (invest_krw / exchange_rate) * yield_pct * exchange_rate
            else:
                display_price = f"{int(price_raw):,}원"
                annual_div_krw = invest_krw * yield_pct
            
            after_tax_div = annual_div_krw * 0.85
            total_dividend_krw += after_tax_div
            
            portfolio_list.append({
                "ticker": item['ticker'], "name": item['name'], "type": item['type'], "weight": f"{weight*100:.1f}%",
                "amount": f"{int(invest_krw):,}원", "price": display_price, "currency": currency,
                "yield": f"{item.get('yield_pct', 0)}%", "expected_div": f"{int(after_tax_div/12):,}원/월", "rationale": item['rationale']
            })

        return jsonify({
            "portfolio": portfolio_list,
            "summary": {
                "monthly_income": f"{int(total_dividend_krw/12):,}원",
                "exchange_rate": f"1달러 = {int(exchange_rate)}원",
                "ai_insight": result.get('ai_insight', '성공적인 투자를 기원합니다.')
            }
        })
    except Exception as e:
        logger.error(f"Portfolio creation error: {e}")
        return jsonify({"error": "AI Error"}), 500
