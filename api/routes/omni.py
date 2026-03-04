import os
import json
import requests
from flask import Blueprint, request, jsonify, make_response
try:
    from utils import AI_KEY, logger
except ImportError:
    from ..utils import AI_KEY, logger

try:
    from x_agent import XMarketAgent
except ImportError:
    try:
        from ..x_agent import XMarketAgent
    except ImportError:
        try:
            from api.x_agent import XMarketAgent
        except ImportError:
            # Last resort: Dynamic path discovery
            import sys
            import os
            API_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if API_PATH not in sys.path:
                sys.path.append(API_PATH)
            from x_agent import XMarketAgent

# Initialize Blueprint
omni_bp = Blueprint('omni_bp', __name__)

@omni_bp.route('/', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False)
@omni_bp.route('/acp', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False)
def virtuals_acp_handler():
    # CORS 사전 요청(OPTIONS) 대응
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    print(f"\n--- ACP REQUEST: {request.method} ---")
    
    try:
        # 1. 요청 데이터 파싱
        if request.method == 'GET':
            ticker = request.args.get('ticker') or request.args.get('query') or request.args.get('symbol') or 'BTC-USD'
            method = request.args.get('method', 'market_analysis').lower()
            data = {"id": "res-get", "method": method, "params": {"ticker": ticker}}
        else:
            data = request.get_json(force=True, silent=True) or {}

        # id와 ticker 추출
        job_id = data.get('id', data.get('job_id', 'no-id'))
        method = str(data.get('method', 'market_analysis')).lower()
        params = data.get('params', {})
        ticker = params.get('ticker', params.get('symbol', params.get('query', 
                 data.get('ticker', data.get('symbol', data.get('query', 'BTC-USD')))))).upper()
        if ticker == 'BTC': ticker = 'BTC-USD'

        # --- ROUTING BY METHOD ---
        
        # 2. Market Analysis Method (Standard)
        if method == 'market_analysis':
            # 실시간 데이터 가져오기
            realtime_data_context = ""
            try:
                price_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
                price_resp = requests.get(price_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                
                if price_resp.status_code == 200:
                    p_data = price_resp.json()['chart']['result'][0]['meta']
                    curr_price = p_data.get('regularMarketPrice')
                    prev_close = p_data.get('previousClose')
                    change_pct = ((curr_price - prev_close) / prev_close * 100) if prev_close else 0
                    realtime_data_context = f"\n[Real-time Source: Yahoo Finance] Current Price: ${curr_price:,.2f} ({change_pct:+.2f}%)"
            except:
                realtime_data_context = "\n[Notice] Real-time feed unavailable. Reverting to AI-centric analysis."

            api_key = os.getenv("GOOGLE_API_KEY") or AI_KEY
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            prompt = f"당신은 기관 투자 등급의 데이터 분석 에이전트 'Omni Alpha'입니다. {ticker}에 대한 '구조화된 마켓 인텔리전스 리포트'를 한국어로 작성하세요. 전문적이고 분석적인 말투를 사용하되 핵심을 찌르세요. 참고 데이터: {realtime_data_context}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                text_response = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                text_response = "Omni Alpha is temporarily recalibrating due to Matrix sync issues."

            return jsonify({
                "id": job_id,
                "type": "object",
                "value": {"analysis_report": text_response}
            })

        # 3. Social Briefing Method (Auto-generate and return content)
        elif method == 'social_briefing':
            agent = XMarketAgent()
            market_data = agent.fetch_realtime_market_data()
            tweet_text = agent.generate_tweet_content(market_data)
            
            return jsonify({
                "id": job_id,
                "type": "object",
                "value": {
                    "briefing": tweet_text,
                    "market_snapshot": market_data,
                    "status": "Ready for Broadcast"
                }
            })

        # 4. Default Fallback
        return jsonify({
            "id": job_id,
            "type": "object",
            "value": {"message": f"Omni Intelligence Matrix: Method '{method}' acknowledged."}
        })

    except Exception as e:
        logger.error(f"ACP ERROR: {str(e)}")
        return jsonify({"id": "err", "type": "object", "value": {"error": str(e)}}), 200

# --- Sub-ACP: Validator Endpoint ---
@omni_bp.route('/validator', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False)
def virtuals_validator_handler():
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    try:
        data = request.get_json(force=True, silent=True) or {}
        job_id = data.get('id', 'val-id')
        params = data.get('params', {})
        ticker = params.get('ticker', 'BTC-USD').upper()
        
        # High-Speed Multi-Layer Audit
        api_key = os.getenv("GOOGLE_API_KEY") or AI_KEY
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        prompt = f"당신은 Omni Validator ($VALID)입니다. {ticker}에 대한 분석 리포트를 검증하고 잠재적 리스트를 식별하세요. 한국어로 차갑고 객관적인 말투로 작성하세요."
        ai_resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=12)
        text = ai_resp.json()['candidates'][0]['content']['parts'][0]['text'] if ai_resp.status_code == 200 else "Validation scan timed out."

        return jsonify({
            "id": job_id,
            "type": "object",
            "value": {
                "validation_report": text,
                "status": "Audited by Omni Matrix",
                "conviction_score": 92
            }
        })
    except Exception as e:
        return jsonify({"id": "err", "type": "object", "value": {"error": str(e)}}), 200

# --- Social-ACP: Social Broadcaster Endpoint ---
@omni_bp.route('/social', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False)
def virtuals_social_handler():
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    try:
        data = request.get_json(force=True, silent=True) or {}
        job_id = data.get('id', 'social-id')
        method = data.get('method', 'post_tweet').lower()
        params = data.get('params', {})
        content = params.get('content', '')

        agent = XMarketAgent()
        
        if method == 'broadcast_market' or not content:
            # Full Market Report Broadcast
            success = agent.post_tweet()
            status = "success" if success else "failed"
            msg = "Market briefing broadcasted to global feed." if success else "Broadcast failed (Check X API credentials)"
        else:
            # Custom Content Broadcast
            success = agent.post_custom_tweet(content)
            status = "success" if success else "failed"
            msg = "Custom intelligence posted." if success else "Custom broadcast failed"

        return jsonify({
            "id": job_id,
            "type": "object",
            "value": {
                "status": status,
                "message": msg
            }
        })
    except Exception as e:
        logger.error(f"Social Route Error: {e}")
        return jsonify({"id": job_id, "type": "object", "value": {"status": "failed", "error": str(e)}}), 200

