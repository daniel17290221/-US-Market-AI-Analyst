#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Market Daily Morning Report Generator v2.0 (Premium News Edition)
Generates a high-end, blog-style report using Gemini AI.
"""

import os
import json
import csv
import logging
import requests
from datetime import datetime, timedelta
# import yfinance as yf (Removed for Vercel stability)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class USDailyReportGenerator:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'report_us.html')
        
        # Configure Gemini
        self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv("google_api_key")
        if self.api_key:
            logger.info("[SUCCESS] Gemini AI (REST) Backend Initialized")
        else:
            logger.warning("[WARNING] GOOGLE_API_KEY not found or default. Using mock data.")

    def fetch_live_indices(self):
        """Fetch live index data using yfinance"""
    def _fetch_yahoo_data(self, symbol):
        """Helper to fetch price data from Yahoo API without yfinance"""
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                result = data.get('chart', {}).get('result')
                if result:
                    meta = result[0].get('meta', {})
                    price = meta.get('regularMarketPrice')
                    prev_close = meta.get('chartPreviousClose', meta.get('previousClose'))
                    
                    if price is not None and prev_close is not None:
                        change_pct = ((price - prev_close) / prev_close) * 100 if prev_close != 0 else 0.0
                        return price, change_pct
            return None, None
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None, None

    def fetch_live_indices(self):
        """Fetch live index data using requests"""
        indices = {
            'SPX500': {'symbol': '^GSPC', 'name': 'S&P 500'},
            'NSXUSD': {'symbol': '^IXIC', 'name': '나스닥'},
            'DJI': {'symbol': '^DJI', 'name': '다우존스'}
        }
        results = {}
        for k, v in indices.items():
            price, change_pct = self._fetch_yahoo_data(v['symbol'])
            if price is not None:
                results[k] = {
                    'name': v['name'],
                    'price': f"{price:,.2f}",
                    'change': f"{change_pct:+.2f}%"
                }
            else:
                results[k] = {'name': v['name'], 'price': 'N/A', 'change': '0.00%'}
        return results

    def fetch_live_commodities(self):
        """Fetch live commodity data using requests"""
        items = [
            {'symbol': 'CL=F', 'name': 'WTI 원유'},
            {'symbol': 'GC=F', 'name': '금 선물'},
            {'symbol': 'BTC-USD', 'name': '비트코인'}
        ]
        results = []
        for item in items:
            price, change_pct = self._fetch_yahoo_data(item['symbol'])
            if price is not None:
                results.append({
                    'name': item['name'],
                    'price': f"{price:,.2f}",
                    'change': f"{change_pct:+.2f}%"
                })
            else:
                results.append({'name': item['name'], 'price': 'N/A', 'change': '0.00%'})
        return results

    def load_data(self):
        """Aggregate data from all available sources"""
        # Fetch live indices and commodities
        live_indices = self.fetch_live_indices()
        live_comms = self.fetch_live_commodities()
        
        data = {
            'date': datetime.now().strftime("%m.%d"),
            'macro': {},
            'market_indices': live_indices,
            'commodities': live_comms,
            'top_stocks': []
        }
        
        # 1. Macro Analysis
        macro_path = os.path.join(self.data_dir, 'us_macro_analysis.json')
        if os.path.exists(macro_path):
            with open(macro_path, 'r', encoding='utf-8') as f:
                data['macro'] = json.load(f)
        
        # 2. Top Stocks (Smart Money)
        # Search for CSV in multiple locations to be robust (local vs vercel)
        possible_csv_paths = [
            os.path.join(self.data_dir, 'smart_money_picks_v2.csv'),
            os.path.join(os.getcwd(), 'us_market', 'smart_money_picks_v2.csv'),
            os.path.join(os.path.dirname(__file__), 'smart_money_picks_v2.csv')
        ]
        
        screener_path = None
        for p in possible_csv_paths:
            if os.path.exists(p):
                screener_path = p
                break

        if screener_path:
            try:
                with open(screener_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    reader.fieldnames = [fn.strip() for fn in reader.fieldnames] if reader.fieldnames else []
                    top_list = list(reader)[:10]  # Get top 10 to allow for some variety or filtering
                    
                    data['top_stocks'] = []
                    for row in top_list:
                        clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
                        ticker_sym = clean_row.get('ticker')
                        if ticker_sym:
                            try:
                                # Fetch live price using the helper to avoid yfinance dependency
                                price, change_pct = self._fetch_yahoo_data(ticker_sym)
                                if price is not None:
                                    clean_row['price'] = f"{price:,.2f}"
                                    clean_row['change'] = f"{change_pct:+.2f}%"
                            except Exception as price_e:
                                logger.warning(f"Failed to refresh price for {ticker_sym}: {price_e}")
                        
                        data['top_stocks'].append(clean_row)
            except Exception as e:
                logger.error(f"Error loading picks: {e}")
                
        return data

    def generate_ai_content(self, raw_data):
        """Synthesize article content via Gemini REST API"""
        if not self.api_key:
            logger.error("❌ [CRITICAL] GOOGLE_API_KEY is missing! Returning MOCK content. Report will NOT be updated with real AI analysis.")
            return self.get_mock_ai_content(raw_data)
            
        prompt = f"""
        당신은 금융 전문 기자와 투자 전략가로 구성된 최고의 리서치 팀입니다. 
        제공된 데이터(JSON)를 바탕으로, 매일 아침 투자자들에게 새로운 시각을 제공하는 '프리미엄 미국 증시 리포트'를 작성하세요.
        
        [특별 지시 - 창의성 및 중복 방지]
        - 이 리포트는 반복적으로 생성됩니다. 기존과 동일한 문투나 뻔한 분석은 지양하세요. 
        - 매번 다른 각도(예: 거시적 관점, 미시적 섹터 순환매, 특정 종목의 드라마틱한 소음 등)에서 이야기를 풀어내세요.
        - 지루한 사실 나열보다는 '스토리텔링'과 '통찰력'을 중시하세요.
        - 현재 시간 기반 변수({datetime.now().strftime('%H시 %M분')})를 분석의 톤에 미세하게 반영하세요. (예: 새벽에는 분석적, 장 중에는 긴박하게)

        데이터:
        {json.dumps(raw_data, ensure_ascii=False, indent=2)}

        [핵심 요구사항 - 반드시 준수!]
        1. **실시간 사건 중심**: '지정학적 리스크' 같은 추상적 단어 대신, {raw_data.get('macro', {}).get('key_takeaways', [])}에 언급된 '실제 사건'을 핵심 키워드로 사용하세요.
        2. **지표와 뉴스 결합**: WTI, 나스닥 등 지표 변동 원인을 데이터의 뉴스 헤드라인과 반드시 연결하세요.
        3. **도발적이고 창의적인 타이틀**: '오늘의 증시' 같이 뻔한 제목 절대 엄금. 뉴스 가치에 기반한 강력하고 지적인 제목을 쓰세요.
        4. **차별화된 섹션**: 기술주, 지정학, 거시 경제 등 매일 데이터 비중이 가장 큰 테마 3가지를 선정하세요.

        [JSON 출력 형식]
        1. catchy_title: 핵심 뉴스를 투영한 강력한 헤드라인
        2. summary_title: 구체적인 시황을 암시하는 창의적인 요약 섹션 제목
        3. core_summary: [긴박한 시황 분석 3문장 (JSON 리스트)]
        4. briefing_title: 역동적인 지수 분석 제목
        5. sections: 최소 3개의 심층 섹션 (emoji_tag, title, content 포함)
        6. hashtags: 관련 해시태그 5개 이상
        7. market_mood_narrative: 한 문장으로 정의하는 오늘의 장 분위기
        """
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "max_output_tokens": 2048
                }
            }
            
            resp = requests.post(url, json=payload, timeout=120)
            if resp.status_code == 200:
                res_json = resp.json()
                text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                logger.info("✅ [SUCCESS] Gemini AI content generated successfully.")
                return json.loads(text)
            else:
                logger.error(f"❌ [CRITICAL] AI API Error: {resp.status_code} - {resp.text[:500]}")
                logger.error("❌ [CRITICAL] Using MOCK content. Report will NOT contain new AI analysis!")
                return self.get_mock_ai_content(raw_data)
        except json.JSONDecodeError as je:
            logger.error(f"❌ [CRITICAL] AI returned invalid JSON: {je}. Using MOCK content.")
            return self.get_mock_ai_content(raw_data)
        except Exception as e:
            logger.error(f"❌ [CRITICAL] AI Generation Error: {e}. Using MOCK content.")
            return self.get_mock_ai_content(raw_data)

    def get_mock_ai_content(self, raw_data):
        """Dynamic fallback mock data for testing"""
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        top_symbol = raw_data['top_stocks'][0]['ticker'] if raw_data['top_stocks'] else "NVDA"
        
        return {
            "catchy_title": f"🔥 [실시간 테스트 {now_time}] {top_symbol}와 빅테크 시장의 새로운 운명",
            "core_summary": [
                f"현재 시각({now_time}) 기준, 실시간 데이터가 정상적으로 수집되었습니다.",
                f"특히 {top_symbol}를 필두로 한 주요 기술주들의 데이터 연동이 성공했습니다.",
                "Gemini API 키가 설정되거나 모델을 2.0으로 변경하면 이 영역이 AI 분석 내용으로 채워집니다."
            ],
            "sections": [
                {
                    "emoji_tag": "🚀",
                    "title": f"실시간 모니터링: {top_symbol} 기술적 분석",
                    "content": f"데이터 수집 결과 {top_symbol}의 가격 흐름이 정상적으로 대시보드에 반영되고 있습니다. (생성 시각: {now_time})"
                },
                {
                    "emoji_tag": "📊",
                    "title": "데이터 수집 파이프라인 정상 보완",
                    "content": "하단의 시장 지수와 원자재 가격이 갱신되었습니다. 브라우저 캐시 문제를 방지하기 위해 매번 시각 정보가 포함된 리포트가 생성됩니다."
                }
            ],
            "hashtags": [f"#{top_symbol}", "#실시간테스트", "#미국증시", "#업데이트성공"],
            "market_mood_narrative": f"데이터 로드 완료 ({now_time}). 모든 시스템이 정상입니다."
        }

    def generate_html(self, raw_data, ai_content):
        """Generate final premium HTML matching the user's blog style"""
        # Set timezone to KST (UTC+9)
        kst_now = datetime.utcnow() + timedelta(hours=9)
        today_date = kst_now.strftime("%Y.%m.%d")
        gen_time = kst_now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Build Index Cards
        indices_html = ""
        for k, v in raw_data['market_indices'].items():
            indices_html += f"""
            <div class="index-card">
                <div class="index-name">📈 {v['name']}</div>
                <div class="index-value">{v['price']}</div>
                <div class="index-change up">{v['change']}</div>
            </div>"""

        # Build News Sections
        sections_html = ""
        for sec in ai_content['sections']:
            sections_html += f"""
            <div class="article-section">
                <div class="section-header">
                    <span class="emoji">{sec['emoji_tag']}</span>
                    <h2>{sec['title']}</h2>
                </div>
                <div class="section-content">
                    <p>{sec['content']}</p>
                </div>
            </div>"""

        # Build Commodity/Crypto Table
        comm_items = ""
        for item in raw_data['commodities']:
            is_up = '+' in item['change']
            change_class = 'up' if is_up else 'down'
            comm_items += f"""
            <div class="market-row">
                <span class="label">{item['name']}</span>
                <span class="val">{item['price']}</span>
                <span class="chg {change_class}">{item['change']}</span>
            </div>"""

        # Build Smart Money Top 5
        smart_money_html = ""
        top_5 = raw_data.get('top_stocks', [])[:5]
        if top_5:
            smart_money_html = """
            <div class="market-brief">
                <div class="brief-title">🎯 스마트 머니 포착: 오늘의 TOP 5 유망주</div>
                <div class="smart-money-grid">
            """
            for stock in top_5:
                # Determine color based on grade
                score = float(stock.get('composite_score', 0))
                score_color = "#ff4d4f" if score >= 80 else ("#faad14" if score >= 70 else "#1890ff")
                
                smart_money_html += f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <span class="ticker">{stock['ticker']}</span>
                        <span class="score" style="color: {score_color}">S:{stock['composite_score']}</span>
                    </div>
                    <div class="stock-name">{stock['name']}</div>
                    <div class="stock-grade">{stock['grade']}</div>
                </div>"""
            smart_money_html += "</div></div>"

        # Build Hashtags
        hashtags_html = " ".join([f'<span class="hashtag">{t}</span>' for t in ai_content.get('hashtags', [])])

        html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>{ai_content['catchy_title']}</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4995156883730033" crossorigin="anonymous"></script>
    <style>
        :root {{
            --bg-color: #f7f9fb;
            --card-bg: #ffffff;
            --text-main: #333333;
            --text-sub: #666666;
            --brand-blue: #0070f3;
            --brand-red: #f44336;
            --brand-green: #4caf50;
            --border-color: #eeeeee;
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #0d1117;
                --card-bg: #161b22;
                --text-main: #e6edf3;
                --text-sub: #8b949e;
                --border-color: #30363d;
            }}
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            background: var(--bg-color); 
            color: var(--text-main); 
            font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
            line-height: 1.6;
            padding: 20px;
        }}
        
        /* Layout Structure */
        .wrapper {{
            display: grid;
            grid-template-columns: 180px minmax(600px, 1000px) 180px;
            justify-content: center;
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .ad-sidebar {{
            width: 180px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            position: sticky;
            top: 20px;
            height: fit-content;
            align-self: flex-start;
        }}

        .ad-unit {{
            background: transparent;
            border: none;
            min-height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: var(--text-sub);
            font-size: 12px;
            padding: 5px;
            overflow: hidden;
        }}

        .container {{
            max-width: 1000px;
            width: 100%;
            background: var(--card-bg);
            padding: 50px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }}

        .category {{ color: var(--brand-blue); font-weight: 800; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }}
        h1 {{ font-size: 32px; line-height: 1.3; margin-bottom: 15px; letter-spacing: -1px; }}
        .date {{ color: var(--text-sub); font-size: 14px; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border-color); }}

        .box-summary {{ 
            background: rgba(0, 112, 243, 0.05); 
            border-radius: 12px; 
            padding: 28px; 
            margin-bottom: 45px; 
            border: 1px solid rgba(0, 112, 243, 0.1); 
        }}
        .box-summary h3 {{ font-size: 18px; margin-bottom: 12px; color: var(--brand-blue); }}
        .box-summary ul {{ list-style-position: inside; }}
        .box-summary li {{ margin-bottom: 8px; color: var(--text-main); font-size: 16px; }}

        .market-indices {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 40px; }}
        .index-card {{ 
            padding: 15px; 
            background: rgba(128,128,128,0.05); 
            border-radius: 10px; 
            text-align: center; 
            border: 1px solid var(--border-color);
        }}
        .index-name {{ font-size: 12px; font-weight: 600; color: var(--text-sub); }}
        .index-value {{ font-size: 18px; font-weight: 800; margin: 4px 0; }}
        .index-change {{ font-size: 14px; font-weight: 600; }}
        .index-change.up {{ color: var(--brand-red); }}
        .index-change.down {{ color: var(--brand-blue); }}

        .article-section {{ margin-bottom: 60px; }}
        .section-header {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px; }}
        .emoji {{ font-size: 28px; }}
        .section-header h2 {{ font-size: 22px; font-weight: 800; line-height: 1.4; }}
        .section-content p {{ font-size: 17px; color: var(--text-main); margin-bottom: 20px; line-height: 1.9; text-align: justify; }}

        .market-brief {{ border-top: 2px solid var(--border-color); padding-top: 30px; margin-bottom: 45px; }}
        .brief-title {{ font-size: 19px; font-weight: 800; margin-bottom: 25px; }}
        .market-row {{ display: flex; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid var(--border-color); font-size: 16px; }}
        .market-row .label {{ font-weight: 600; }}
        .market-row .val {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; }}
        .market-row .chg.up {{ color: var(--brand-red); }}
        .market-row .chg.down {{ color: var(--brand-blue); }}

        .hashtags {{ margin-top: 50px; padding-top: 25px; border-top: 1px solid var(--border-color); }}
        .hashtag {{ color: var(--text-sub); font-size: 15px; margin-right: 20px; font-weight: 600; }}

        /* Smart Money Grid */
        .smart-money-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 20px; }}
        .stock-card {{ 
            padding: 12px; 
            background: rgba(128,128,128,0.03); 
            border-radius: 10px; 
            border: 1px solid var(--border-color);
            transition: transform 0.2s;
        }}
        .stock-card:hover {{ transform: translateY(-3px); }}
        .stock-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }}
        .stock-header .ticker {{ font-weight: 900; font-size: 14px; }}
        .stock-header .score {{ font-size: 10px; font-weight: 800; }}
        .stock-name {{ font-size: 10px; color: var(--text-sub); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .stock-grade {{ font-size: 10px; font-weight: 700; margin-top: 5px; color: var(--text-main); }}

        @media (max-width: 768px) {{
            .smart-money-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}

        .footer {{ margin-top: 70px; text-align: center; font-size: 13px; color: var(--text-sub); border-top: 1px solid var(--border-color); padding-top: 30px; }}

        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}

        .ad-banner-bottom {{ 
            width: 100%;
            background: rgba(10, 10, 10, 0.5);
            border-top: 1px solid var(--border-color);
            padding: 20px 12px;
            margin-top: 40px;
            text-align: center;
        }}

        @media (max-width: 1200px) {{
            .ad-sidebar {{ display: none; }}
            .container {{ max-width: 100%; padding: 30px 20px; }}
            .container {{ min-width: 100%; }}
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4995156883730033" crossorigin="anonymous"></script>
</head>
<body>
    <div class="wrapper">
        <!-- Left Sidebar for Ads (AdSense) -->
        <aside class="ad-sidebar">
            <div class="ad-unit">
                <!-- 바이브코딩랩 PC좌측 사이드바 -->
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-4995156883730033"
                     data-ad-slot="7174591391"
                     data-ad-format="vertical"
                     data-full-width-responsive="true"></ins>
                <script>
                     (adsbygoogle = window.adsbygoogle || []).push({{}});
                </script>
            </div>
        </aside>

        <div class="container">
            <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 25px;">
                <span style="background: #f44336; color: white; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; animation: pulse 2s infinite; letter-spacing: 1px;">
                    🔴 LIVE UPDATED: {gen_time}
                </span>
            </div>
            <div class="category">Daily Morning Report</div>
            <h1>{ai_content['catchy_title']}</h1>
            <div class="date">{today_date} • Premium AI Analysis</div>

            <div class="box-summary">
                <h3>{ai_content.get('summary_title', '오늘의 마켓 체크포인트')}</h3>
                <ul>
                    { "".join([f'<li>{line}</li>' for line in (ai_content['core_summary'] if isinstance(ai_content['core_summary'], list) else [ai_content['core_summary']])]) }
                </ul>
            </div>

            <div class="market-brief">
                <div class="brief-title">{ai_content.get('briefing_title', '미국 증시 브리핑')}: {raw_data['date']} 장마감 기준</div>
                <div class="market-indices">
                    {indices_html}
                </div>
            </div>

            {sections_html}

            {smart_money_html}

            <div class="market-brief">
                <div class="brief-title">주요 원자재 및 암호화폐 시황</div>
                {comm_items}
            </div>

            <div class="hashtags">
                {hashtags_html}
            </div>

            <div class="footer">
                🚀 본 리포트는 VibeCodingLab 종목 분석 AI 시스템에 의해 실시간 데이터 집계 및 분석되었습니다.<br>
                <b>생성 시각: {gen_time}</b> (KST 한국 시각 반영 완료)<br>
                © 2026 VibeCodingLab. All Rights Reserved.
            </div>
        </div>

        <!-- Right Sidebar for Ads -->
        <aside class="ad-sidebar">
            <div class="ad-unit">
                <!-- 바이브코딩랩 데일리 리포트 우측 -->
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-4995156883730033"
                     data-ad-slot="7174591391"
                     data-ad-format="vertical"
                     data-full-width-responsive="true"></ins>
                <script>
                     (adsbygoogle = window.adsbygoogle || []).push({{}});
                </script>
            </div>
        </aside>
    </div>

    <div class="ad-banner-bottom">
        <!-- 바이브코딩랩 데일리 리포트 하단 전면 -->
        <ins class="adsbygoogle"
             style="display:inline-block;width:728px;height:90px"
             data-ad-client="ca-pub-4995156883730033"
             data-ad-slot="7174591391"
             data-full-width-responsive="true"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({{}});
        </script>
    </div>
</body>
</html>
        """
        # Add a forced timestamp to ensure git always detects a change
        html_template += f"\n<!-- US Generation ID: {datetime.now().isoformat()} -->"
        
        # 1. Local Filesystem Write
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(html_template)
            logger.info(f"✅ [SUCCESS] US report saved locally to: {self.output_file}")
            logger.info(f"✅ [SUCCESS] US report size: {len(html_template)} bytes")
        except Exception as write_e:
            logger.error(f"❌ [ERROR] Could not write US report locally: {write_e}")
            raise  # Re-raise so the GitHub Actions step fails visibly
            
        # 2. GitHub Pages Repo Write (local env only, GitHub Actions workflow handles this)
        try:
            self._deploy_to_github_pages(html_template)
        except Exception as e:
            logger.warning(f"[WARN] _deploy_to_github_pages failed (ignored): {e}")
            
        return html_template

    def _deploy_to_github_pages(self, html_content):
        """생성된 리포트를 GitHub Pages 레포에 복사하고 git push 합니다."""
        import subprocess

        # GitHub Actions already deployed via the workflow file. 
        # Skipping this to avoid duplicate commits and submodule conflicts.
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            logger.info("[DEPLOY] Skipping Python-based deploy in GitHub Actions environment.")
            return

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            pages_repo = os.path.join(project_root, 'temp_pages_repo')

            if not os.path.isdir(pages_repo):
                logger.warning(f"[DEPLOY] GitHub Pages repo not found at: {pages_repo}")
                return

            # ★ GitHub Desktop 등 수동 push와의 충돌 방지: 파일 쓰기 전에 원격 변경사항 먼저 반영
            pull_result = subprocess.run(
                ['git', 'pull', '--rebase', 'origin', 'main'],
                cwd=pages_repo, capture_output=True, text=True,
                timeout=30, encoding='utf-8', errors='replace'
            )
            if pull_result.returncode != 0:
                logger.warning(f"[DEPLOY] pull 실패, 강제 리셋: {pull_result.stderr[:200]}")
                subprocess.run(['git', 'rebase', '--abort'], cwd=pages_repo, capture_output=True)
                subprocess.run(['git', 'fetch', 'origin'], cwd=pages_repo, capture_output=True)
                subprocess.run(['git', 'reset', '--hard', 'origin/main'], cwd=pages_repo, capture_output=True)

            target_file = os.path.join(pages_repo, 'report_us.html')
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"[DEPLOY] report_us.html 작성 완료")

            today = datetime.now().strftime('%Y-%m-%d %H:%M')
            cmds = [
                ['git', 'add', 'report_us.html'],
                ['git', 'commit', '-m', f'auto: US 데일리 리포트 업데이트 ({today})'],
                ['git', 'push', 'origin', 'main'],
            ]
            for cmd in cmds:
                result = subprocess.run(
                    cmd, cwd=pages_repo, capture_output=True, text=True,
                    timeout=30, encoding='utf-8', errors='replace'
                )
                if result.returncode != 0:
                    if 'nothing to commit' in (result.stdout + result.stderr):
                        logger.info("[DEPLOY] 변경사항 없음 (스킵)")
                        break
                    logger.warning(f"[DEPLOY] git 명령 실패: {' '.join(cmd)}\n{result.stderr[:200]}")
                    break
                logger.info(f"[DEPLOY] OK: {' '.join(cmd)}")

            logger.info("[DEPLOY] ✅ US 리포트 배포 완료!")
        except Exception as e:
            logger.warning(f"[DEPLOY] US 배포 실패 (무시): {e}")

    def run(self):
        logger.info("Generating Premium Daily US Market Report...")
        try:
            raw_data = self.load_data()
            ai_content = self.generate_ai_content(raw_data)
            return self.generate_html(raw_data, ai_content)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"[FATAL] Report generation crashed: {error_trace}")
            
            # Generate a blank error HTML to force the action to commit it, exposing the error!
            html_template = f"<html><body><h1>Fatal Error in US Generator</h1><pre>{error_trace}</pre>\n<!-- Generation ID: {datetime.now().isoformat()} --></body></html>"
            
            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(html_template)
            except:
                pass
            return html_template


if __name__ == "__main__":
    # If run directly as a script, default to its own directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    USDailyReportGenerator(data_dir=base_dir).run()
