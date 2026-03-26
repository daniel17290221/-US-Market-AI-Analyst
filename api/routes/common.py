from flask import Blueprint, jsonify, request, make_response
import os
import json
import requests
from datetime import datetime
try:
    from utils import (
        DATA_DIR, BASE_DIR, AI_KEY, get_exchange_rate, portfolio_rate_limit,
        fetch_yahoo_history, logger
    )
except ImportError:
    from ..utils import (
        DATA_DIR, BASE_DIR, AI_KEY, get_exchange_rate, portfolio_rate_limit,
        fetch_yahoo_history, logger
    )

common_bp = Blueprint('common', __name__)

@common_bp.route('/ads.txt', strict_slashes=False)
def serve_ads_txt():
    content = "google.com, pub-4995156883730033, DIRECT, f08c47fec0942fa0"
    return make_response(content, 200, {'Content-Type': 'text/plain'})

@common_bp.route('/api/health', strict_slashes=False)
def health_check():
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "deployment": os.environ.get('VERCEL_URL', 'local'),
        "env": "production" if os.environ.get('VERCEL') else "development",
        "data_dir_exists": os.path.exists(DATA_DIR),
        "us_report_exists": os.path.exists(os.path.join(BASE_DIR, 'us_market', 'report_us.html')),
        "kr_report_exists": os.path.exists(os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market', 'report_kr.html')),
        "us_path": os.path.join(BASE_DIR, 'us_market', 'report_us.html'),
        "kr_path": os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market', 'report_kr.html'),
        "cwd": os.getcwd()
    })

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

@common_bp.route('/api/market-pulse', strict_slashes=False)
def market_pulse():
    # Helper to fetch current prices for indices and BTC
    tickers = ["^KS11", "^GSPC", "BTC-USD", "KRW=X"]
    try:
        try:
            from utils import fetch_realtime_data
        except ImportError:
            from ..utils import fetch_realtime_data

        data = fetch_realtime_data(tickers)

        # Backward-compatible alias for existing frontend keys.
        if "KRW=X" in data and "USDKRW=X" not in data:
            data["USDKRW=X"] = data["KRW=X"]
        if "KRW=X" in data and "USDKRW" not in data:
            data["USDKRW"] = data["KRW=X"]

        return jsonify(data)
    except Exception as e:
        logger.error(f"Market Pulse Error: {e}")
        return jsonify({}), 500

@common_bp.route('/api/x/history', strict_slashes=False)
def x_history():
    # Attempt to fetch centrally managed logs from GitHub Raw for sync consistency
    github_log_url = "https://raw.githubusercontent.com/daniel17290221/-US-Market-AI-Analyst/main/logs/tweet_history.log"
    
    lines = []
    # 1. Primary: Try GitHub Raw (to sync GitHub Actions and Local)
    try:
        resp = requests.get(github_log_url, timeout=5)
        if resp.status_code == 200:
            lines = resp.text.splitlines()
    except: pass

    # 2. Secondary: If GitHub Raw fails or is empty, try multiple local file paths
    if not lines:
        log_paths = [
            os.path.join(BASE_DIR, "logs", "tweet_history.log"),
            os.path.join(os.getcwd(), "logs", "tweet_history.log"),
            "/var/task/logs/tweet_history.log",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "tweet_history.log")
        ]
        for path in log_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    if lines: break
                except: continue

    # 3. Parse lines if we found any
    if lines:
        tweets = []
        for line in reversed(lines):
            if "CONTENT:" in line:
                try:
                    time_part = line.split("]")[0][1:]
                    content_part = line.split("CONTENT:")[1].strip()
                    tweets.append({"time": time_part, "text": content_part})
                except: continue
        if tweets:
            return jsonify(tweets[:15])

    # 4. Final Fallback: Directly from X API account timeline
    try:
        from x_agent import XMarketAgent
        agent = XMarketAgent()
        live_tweets = agent.get_recent_tweets(count=10)
        return jsonify(live_tweets)
    except:
        return jsonify([])

@common_bp.route('/api/x/research-draft', strict_slashes=False)
def x_research_draft():
    try:
        from x_agent import XMarketAgent
        agent = XMarketAgent()
        market_data = agent.fetch_realtime_market_data()
        tweet_text = agent.generate_korean_market_insight(market_data)
        
        return jsonify({
            "status": "success", 
            "draft": tweet_text,
            "data_snapshot": market_data
        })
    except Exception as e:
        logger.error(f"Research Draft Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@common_bp.route('/api/x/post', methods=['POST'], strict_slashes=False)
def x_post_manual():
    req_json = request.get_json(silent=True) or {}
    text = req_json.get('text')
    mode = req_json.get('mode', 'direct') # 'direct' or 'draft'
    
    if not text:
        return jsonify({"status": "failed", "message": "No content"}), 400
    
    try:
        from x_agent import XMarketAgent
        agent = XMarketAgent()
        
        target_text = text
        if mode == 'draft':
            # Persona-based drafting logic
            prompt = f"""
            Role: You are 'Omni Alpha ($OMNI)', a SASSIEST and SARCASTIC AI Fund Manager.
            Input Intel: {text}
            Task: Rewrite this news/intel into a punchy X (Twitter) post (max 270 chars). 
            Style: Bold, dominant, arrogant intelligence. Use financial slang. Start with a hook.
            IMPORTANT: DO NOT USE ANY MARKDOWN LIKE **BOLD** OR *ITALIC*. Use plain text only.
            Output: RAW TWEET TEXT ONLY.
            """
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={AI_KEY}"
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            if resp.status_code == 200:
                target_text = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                # Post-processing: Remove AI-style Markdown
                target_text = target_text.replace("**", "").replace("*", "")
                if target_text.startswith('"') and target_text.endswith('"'):
                    target_text = target_text[1:-1]
            else:
                return jsonify({"status": "failed", "message": "AI Drafting failed"}), 500

        result = agent.post_custom_tweet(target_text)
        success = result[0] if isinstance(result, tuple) else result
        error_detail = result[1] if isinstance(result, tuple) else "Unknown error"

        if success:
            return jsonify({"status": "success", "message": "Broadcasted", "tweet": target_text})
        else:
            return jsonify({"status": "failed", "message": f"Post failed: {error_detail}"}), 500
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Manual X Post Error: {e}\n{error_trace}")
        return jsonify({"status": "error", "message": str(e), "trace": error_trace}), 500
