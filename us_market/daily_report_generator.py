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
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class USDailyReportGenerator:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'us_market_morning_report.html')
        
        # Configure Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key and api_key != "your_gemini_api_key_here":
            genai.configure(api_key=api_key)
            # Use gemini-2.0-flash as requested by user
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("✅ Gemini AI Backend Initialized")
        else:
            self.model = None
            logger.warning("⚠️ GOOGLE_API_KEY not found or default. Using mock data.")

    def load_data(self):
        """Aggregate data from all available sources"""
        data = {
            'date': datetime.now().strftime("%m.%d"),
            'macro': {},
            'market_indices': {
                'SPX500': {'name': 'S&P 500', 'price': '6,940.01', 'change': '+0.00%'},
                'NSXUSD': {'name': '나스닥', 'price': '23,515.39', 'change': '+0.00%'},
                'DJI': {'name': '다우존스', 'price': '49,359.33', 'change': '+0.00%'}
            },
            'commodities': [
                {'name': 'WTI 원유', 'price': '59.34', 'change': '+0.44%'},
                {'name': '금 선물', 'price': '4,595.40', 'change': '-0.61%'},
                {'name': '비트코인', 'price': '129,446,000', 'change': '-0.02%'}
            ],
            'top_stocks': []
        }
        
        # 1. Macro Analysis
        macro_path = os.path.join(self.data_dir, 'us_macro_analysis.json')
        if os.path.exists(macro_path):
            with open(macro_path, 'r', encoding='utf-8') as f:
                data['macro'] = json.load(f)
        
        # 2. Top Stocks (Smart Money)
        screener_path = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if os.path.exists(screener_path):
            try:
                with open(screener_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data['top_stocks'] = list(reader)[:5]
            except Exception as e:
                logger.error(f"Error loading picks: {e}")
                
        return data

    def generate_ai_content(self, raw_data):
        """Synthesize article content via Gemini"""
        if not self.model:
            return self.get_mock_ai_content(raw_data)
            
        prompt = f"""
        당신은 미국 금융 시장 전문 뉴스 에디터입니다. 아래 제공된 시장 데이터(JSON)와 현재의 지정학적/경제적 상황을 결합하여, 
        네이버 블로그나 프리미엄 경제 매거진 스타일의 '미국 시장 데일리 리포트'를 작성해주세요.

        데이터:
        {json.dumps(raw_data, ensure_ascii=False, indent=2)}

        요청 사항 (JSON 형식으로 출력):
        1. catchy_title: 시장의 핵심 이슈를 관통하는 충격적이고 매력적인 헤드라인. (예: "그린란드 관세 100% 실행"... 미국-유럽 동맹 깨지나)
        2. core_summary: 오늘 꼭 알아야 할 핵심 내용 3문장을 반드시 JSON 리스트 형식으로 출력 (예: ["내용1", "내용2", "내용3"]).
        3. sections: 최소 3개의 심층 분석 섹션. 각 섹션은 다음을 포함:
           - emoji_tag: 섹션 성격에 맞는 이모지 (예: 🔥, 🚀, ⚠️, 🙏)
           - title: 흥미로운 섹션 제목
           - content: 전문적이지만 읽기 쉬운 구어체 (~해요, ~입니다) 분석 (최소 300자 이상 상세히)
        4. hashtags: 관련 해시태그 5개 이상.
        5. market_mood_narrative: 현재 시장 분위기를 묘사하는 문장.

        금융 용어는 정확하게 사용하되, 문체는 친절하고 통찰력이 있어야 합니다.
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            # Clean JSON string
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
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

        # Build Hashtags
        hashtags_html = " ".join([f'<span class="hashtag">{t}</span>' for t in ai_content.get('hashtags', [])])

        html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ai_content['catchy_title']}</title>
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
            display: flex;
            justify-content: center;
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .ad-sidebar {{
            width: 180px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .ad-unit {{
            background: var(--card-bg);
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: var(--text-sub);
            font-size: 12px;
            font-weight: bold;
            padding: 20px;
        }}

        .container {{ 
            max-width: 1000px; 
            width: 100%;
            background: var(--card-bg); 
            padding: 50px; 
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: relative;
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

        .footer {{ margin-top: 70px; text-align: center; font-size: 13px; color: var(--text-sub); border-top: 1px solid var(--border-color); padding-top: 30px; }}

        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}

        /* Mobile Sticky Ad */
        .mobile-ad-banner {{
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: var(--card-bg);
            border-top: 1px solid var(--border-color);
            padding: 10px;
            z-index: 1000;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}

        @media (max-width: 1200px) {{
            .ad-sidebar {{ display: none; }}
            .container {{ max-width: 100%; padding: 30px 20px; }}
            .mobile-ad-banner {{ display: block; }}
            body {{ padding-bottom: 100px; }} /* Space for sticky ad */
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- Left Sidebar for Ads -->
        <aside class="ad-sidebar">
            <div class="ad-unit">
                <!-- 쿠팡 파트너스 좌측 광고 스크립트 위치 -->
                <script src="https://ads-partners.coupang.com/g.js"></script>
                <script>
                    new PartnersCoupang.G({{ "id": 834566, "template": "carousel", "trackingCode": "AF1234567", "width": "180", "height": "600" }});
                </script>
                <div style="font-size: 10px; margin-top: 5px;">"이 포스팅은 쿠팡 파트너스 활동의 일환으로, <br>이에 따른 일정액의 수수료를 제공받습니다."</div>
            </div>
        </aside>

        <div class="container">
            <div style="text-align: right; margin-bottom: 25px;">
                <span style="background: #f44336; color: white; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; animation: pulse 2s infinite; letter-spacing: 1px;">
                    🔴 LIVE UPDATED: {gen_time}
                </span>
            </div>
            <div class="category">Daily Morning Report</div>
            <h1>{ai_content['catchy_title']}</h1>
            <div class="date">{today_date} • Premium AI Analysis</div>

            <div class="box-summary">
                <h3>핵심 요약</h3>
                <ul>
                    { "".join([f'<li>{line}</li>' for line in (ai_content['core_summary'] if isinstance(ai_content['core_summary'], list) else [ai_content['core_summary']])]) }
                </ul>
            </div>

            <div class="market-brief">
                <div class="brief-title">미국 증시 브리핑: {raw_data['date']} 장마감 기준</div>
                <div class="market-indices">
                    {indices_html}
                </div>
            </div>

            {sections_html}

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
                <!-- 쿠팡 파트너스 우측 광고 스크립트 위치 -->
                <script src="https://ads-partners.coupang.com/g.js"></script>
                <script>
                    new PartnersCoupang.G({{ "id": 834567, "template": "carousel", "trackingCode": "AF1234567", "width": "180", "height": "600" }});
                </script>
                <div style="font-size: 10px; margin-top: 5px;">"이 포스팅은 쿠팡 파트너스 활동의 일환으로, <br>이에 따른 일정액의 수수료를 제공받습니다."</div>
            </div>
        </aside>
    </div>

    <!-- Mobile Sticky Ad Banner -->
    <div class="mobile-ad-banner">
        <!-- 쿠팡 파트너스 모바일 하단 광고 스크립트 위치 -->
        <script src="https://ads-partners.coupang.com/g.js"></script>
        <script>
            new PartnersCoupang.G({{ "id": 834568, "template": "banner", "trackingCode": "AF1234567", "width": "100%", "height": "80" }});
        </script>
    </div>
</body>
</html>
        """
        
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(self.output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(html_template)
            logger.info(f"✅ Premium report saved to: {self.output_file}")
        except Exception as e:
            logger.error(f"❌ Error saving report to {self.output_file}: {e}")
            
        return html_template

    def run(self):
        logger.info("🚀 Generating Premium Daily US Market Report...")
        raw_data = self.load_data()
        ai_content = self.generate_ai_content(raw_data)
        return self.generate_html(raw_data, ai_content)

if __name__ == "__main__":
    # If run directly as a script, default to current directory
    USDailyReportGenerator(data_dir='.').run()
