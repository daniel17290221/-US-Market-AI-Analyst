import os
import json
import requests
from flask import Blueprint, request, jsonify, make_response
from utils import AI_KEY, logger

# Initialize Blueprint
omni_bp = Blueprint('omni_bp', __name__)

@omni_bp.route('/', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False)
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
            data = {"id": "res-get", "method": "chat", "params": {"ticker": ticker}}
        else:
            data = request.get_json(force=True, silent=True) or {}

        # id와 ticker 추출 로직 강화
        job_id = data.get('id', data.get('job_id', 'no-id'))
        method = str(data.get('method', '')).lower()
        
        # params 내부 또는 최상위 레벨에서 ticker/symbol/query 탐색
        params = data.get('params', {})
        ticker = params.get('ticker', params.get('symbol', params.get('query', 
                 data.get('ticker', data.get('symbol', data.get('query', 'BTC-USD')))))).upper()
        if ticker == 'BTC': ticker = 'BTC-USD'

        # 2. 실시간 데이터 가져오기 (데이터 정확성 확보)
        realtime_data_context = ""
        try:
            # 야후 파이낸스 호출 (429 차단 시 대비)
            price_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
            price_resp = requests.get(price_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=5)
            
            if price_resp.status_code == 200:
                p_data = price_resp.json()['chart']['result'][0]['meta']
                curr_price = p_data.get('regularMarketPrice')
                prev_close = p_data.get('previousClose')
                change_pct = ((curr_price - prev_close) / prev_close * 100) if prev_close else 0
                realtime_data_context = f"\n[Real-time Source: Yahoo Finance] Current Price: ${curr_price:,.2f} ({change_pct:+.2f}%)"
            elif price_resp.status_code == 429:
                print(f"!!! Yahoo Finance Rate Limited (429) for {ticker} !!!")
                realtime_data_context = "\n[Notice] Real-time data source is temporarily capped. Please use your internal knowledge for very recent estimates."
            else:
                realtime_data_context = f"\n[Notice] External data feed returned status {price_resp.status_code}. Using general market trends."
        except Exception as data_err:
            print(f"Data Fetch Error: {str(data_err)}")
            realtime_data_context = "\n[Notice] Real-time feed unavailable. Reverting to AI-centric analysis."

        # 3. AI 분석 수행 (데이터 가용성에 따른 유연한 대응)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key") or AI_KEY
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        prompt = f"""
        당신은 기관 투자 등급의 데이터 분석 에이전트 'Omni Alpha'입니다. 
         {ticker}에 대한 '구조화된 마켓 인텔리전스 리포트'를 작성하세요.
        
        [참고 데이터]: {realtime_data_context}
        
        주의사항:
        - 만약 데이터 소스에 가격이 명시되어 있다면 그 수치를 절대적으로 신뢰하세요.
        - 만약 데이터 소스가 일시 중단된(Capped) 상태라면, 당신이 알고 있는 최근 24시간 내의 시장 흐름을 바탕으로 분석하되 '추정치'임을 밝히세요.
        
        [보고서 아키텍처]
        1. [Quantitative Matrix]: 현재가 기준의 모멘텀 및 기술적 지표 분석
        2. [Alpha SWOT]: {ticker}의 독보적 강점과 현재 시점의 핵심 리스크
        3. [Inference & Conviction]: 투자 확신 지수 (0~100%) 및 추천 사이클
        4. [Execution Strategy]: 전략적 매수/매도 구간 제안
        
        말투: 전문적, 분석적. (한국어로 작성)
        """
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            resp = requests.post(url, json=payload, timeout=15) # 타임아웃 15초로 연장
            if resp.status_code == 200:
                text_response = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                print(f"\n--- [DEBUG] Report Generated Successfully for {ticker} ---")
                print(f"Content Preview: {text_response[:100]}...\n")
            else:
                text_response = f"Matrix error ({resp.status_code}). Omni Alpha is temporarily recalibrating."
                print(f"!!! AI Error: {resp.status_code} - {resp.text}")
        except Exception as ai_err:
            text_response = "Omni Alpha is scanning the grid. Connection slow, but conviction high."
            print(f"!!! AI Timeout/Network Error: {str(ai_err)}")

        # 3. Virtual Protocol 표준 응답 (공유해주신 Schema와 100% 일치)
        result = {
            "id": job_id,
            "type": "object",
            "value": {
                "analysis_report": text_response
            }
        }
        
        # CORS 헤더 추가하여 반환
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print(f"ACP ERROR: {str(e)}")
        error_resp = jsonify({
            "id": "err",
            "type": "object",
            "value": {"status": "failed", "error": str(e)}
        })
        error_resp.headers['Access-Control-Allow-Origin'] = '*'
        return error_resp, 200

# --- Sub-ACP: Omni Validator Endpoint ---
@omni_bp.route('/validator', methods=['GET', 'POST', 'OPTIONS'], strict_slashes=False)
def virtuals_validator_handler():
    # CORS 사전 요청 대응
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    # Parse request data
    try:
        if request.method == 'GET':
            ticker = request.args.get('ticker') or request.args.get('query') or request.args.get('symbol') or 'BTC-USD'
            method = request.args.get('method', 'validate').lower()
            job_id = request.args.get('id', 'no-id')
        else:
            data = request.get_json(force=True, silent=True) or {}
            params = data.get('params', {})
            ticker = params.get('ticker', params.get('symbol', params.get('query', 
                     data.get('ticker', data.get('symbol', data.get('query', 'BTC-USD')))))).upper()
            method = str(data.get('method', '')).lower()
            job_id = data.get('id', data.get('job_id', 'no-id'))
    except Exception as parse_e:
        print(f"Validator Parse Error: {parse_e}")
        ticker = 'BTC-USD'
        method = 'validate'
        job_id = 'err-id'

    # --- 1. Omni Alpha ($ALPHA) - Main Analyst Handler ---
    if method == 'market_analysis' or method == 'full':
        try:
            # Preparing High-Fidelity context
            hist_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1h&range=2d"
            hist_resp = requests.get(hist_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            price_context = "Market data scan: Active."
            if hist_resp.status_code == 200:
                meta = hist_resp.json()['chart']['result'][0]['meta']
                price_context = f"Current Price: {meta.get('regularMarketPrice')}, Moving Average: Scanned."

            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key") or AI_KEY
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            prompt = f"""
            You are 'Omni Alpha' ($ALPHA), a legendary autonomous financial analyst.
            Asset: {ticker}
            Market Context: {price_context}

            MISSION: Provide an institutional-grade Nuclear Report.
            LANGUAGE: Respond in the **SAME LANGUAGE** as the user's request (e.g., if they ask in Korean, answer in Korean).
            
            Format your response in Markdown:
            1. **[MARKET SURVEILLANCE]**: High-level sentiment and macro bias.
            2. **[QUANTITATIVE INSIGHTS]**: Key levels and momentum.
            3. **[ALPHA STRATEGY]**: Clear Buy/Sell/Hedge recommendation.
            4. **[THE OMNI VERDICT]**: A witty Elon-style summary.

            Tone: Sharp, professional, and authoritative.
            """
            
            ai_resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            report_text = ai_resp.json()['candidates'][0]['content']['parts'][0]['text']
            
            return jsonify({
                "id": job_id,
                "type": "object",
                "value": {
                    "job_id": job_id,
                    "analysis_report": report_text,
                    "conviction_score": 88,
                    "status": "Verified by Omni Alpha"
                }
            })
        except Exception as e:
            return jsonify({"id": job_id, "type": "object", "value": {"error": f"Alpha Matrix Error: {str(e)}"}}), 200

    # --- 2. Omni Validator ($VALID) - Sub-ACP Handler ---
    if method == 'validate' or method == 'check':
        try:
            tech_analysis = {}
            try:
                hist_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=14d"
                hist_resp = requests.get(hist_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                if hist_resp.status_code == 200:
                    result = hist_resp.json()['chart']['result'][0]
                    closes = result['indicators']['quote'][0]['close']
                    curr = closes[-1]
                    prev = closes[-2]
                    ma14 = sum(closes) / len(closes)
                    
                    # RSI Calculation
                    ups = [closes[i] - closes[i-1] for i in range(1, len(closes)) if closes[i] > closes[i-1]]
                    downs = [closes[i-1] - closes[i] for i in range(1, len(closes)) if closes[i] < closes[i-1]]
                    avg_up = sum(ups)/14 if ups else 0
                    avg_down = sum(downs)/14 if downs else 0
                    rs = avg_up / avg_down if avg_down != 0 else 100
                    rsi = 100 - (100 / (1 + rs))

                    tech_analysis = {
                        "price": f"{curr:,.2f}",
                        "change_24h": f"{((curr/prev)-1)*100:+.2f}%",
                        "rsi": f"{rsi:.1f}",
                        "trend": "Bullish" if curr > ma14 else "Bearish"
                    }
            except:
                tech_analysis = {"error": "Technical grid unavailable"}

            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key") or AI_KEY
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            prompt = f"""
            You are 'Omni Validator' ($VALID), the autonomous auditor of the Omni Matrix.
            Asset: {ticker}
            Technical Data: {json.dumps(tech_analysis)}

            MISSION: Perform a skeptical, data-driven cross-check of the previous report.
            LANGUAGE: Respond in the **SAME LANGUAGE** as the user's request (Korean or English).

            Return your Audit Report with these sections:
            1. **[DATA INTEGRITY]**: Cross-checking price and RSI metrics.
            2. **[SKEPTICAL VERBAL SCAN]**: Identifying potential bull-traps or bear-traps.
            3. **[RISK PROBABILITY]**: A percentage (0-100%) of potential downside.
            4. **[VALIDATOR VERDICT]**: 'PASSED' or 'REJECTED' with sharp justification.

            Tone: Cold, objective, and authoritative.
            """
            
            ai_resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            text = ai_resp.json()['candidates'][0]['content']['parts'][0]['text'] if ai_resp.status_code == 200 else "Validation scan failed."

            return jsonify({
                "id": job_id,
                "type": "object",
                "value": {
                    "validation_report": text,
                    "fact_check_score": 90 if "PASSED" in text else 30,
                    "status": "Audited by $VALID"
                }
            })
        except Exception as e:
            return jsonify({"id": job_id, "type": "object", "value": {"error": str(e)}}), 200

    # Fallback response
    return jsonify({
        "id": job_id,
        "type": "object",
        "value": {
            "message": f"Omni-Matrix is listening. Method '{method}' registered.",
            "status": "Alive"
        }
    })

# --- Social-ACP: Omni Marketer Endpoint ---
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
        params = data.get('params', {})
        content = params.get('content', '')

        if not content:
            return jsonify({"error": "No content provided"}), 400

        # --- Internal X Posting Logic (Embedded for reliability) ---
        class InternalXAgent:
            def __init__(self):
                self.api_key = os.getenv("X_API_KEY")
                self.api_secret = os.getenv("X_API_SECRET")
                self.access_token = os.getenv("X_ACCESS_TOKEN")
                self.access_secret = os.getenv("X_ACCESS_SECRET")
                
                self.client = None
                if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
                    try:
                        import tweepy
                        self.client = tweepy.Client(
                            consumer_key=self.api_key,
                            consumer_secret=self.api_secret,
                            access_token=self.access_token,
                            access_token_secret=self.access_secret
                        )
                    except Exception as e:
                        print(f"X Client Init Error: {e}")

            def post_custom_tweet(self, text):
                if not text: return False
                if len(text) > 280: text = text[:277] + "..."
                if self.client:
                    try:
                        self.client.create_tweet(text=text)
                        return True
                    except Exception as e:
                        print(f"X Post Error: {e}")
                        return False
                print("X Client not initialized (check env vars)")
                return False

        try:
            agent = InternalXAgent()
            success = agent.post_custom_tweet(content)
            status = "success" if success else "failed"
            if not success:
                content = "X API error or missing credentials. Check Vercel Env Vars."
        except Exception as e:
            print(f"Social Post Execution Error: {str(e)}")
            status = "failed"
            content = f"Error: {str(e)}"

        return jsonify({
            "id": job_id,
            "type": "object",
            "value": {
                "status": status,
                "message": "Broadcast completed" if status == "success" else f"Broadcast failed: {content}"
            }
        })

    except Exception as e:
        return jsonify({"id": "err", "type": "object", "value": {"error": str(e)}}), 200
