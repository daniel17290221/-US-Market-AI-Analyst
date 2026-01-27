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
from datetime import datetime
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
            return self.get_mock_ai_content()
            
        prompt = f"""
        당신은 미국 금융 시장 전문 뉴스 에디터입니다. 아래 제공된 시장 데이터(JSON)와 현재의 지정학적/경제적 상황을 결합하여, 
        네이버 블로그나 프리미엄 경제 매거진 스타일의 '미국 시장 데일리 리포트'를 작성해주세요.

        데이터:
        {json.dumps(raw_data, ensure_ascii=False, indent=2)}

        요청 사항 (JSON 형식으로 출력):
        1. catchy_title: 시장의 핵심 이슈를 관통하는 충격적이고 매력적인 헤드라인. (예: "그린란드 관세 100% 실행"... 미국-유럽 동맹 깨지나)
        2. core_summary: 오늘 꼭 알아야 할 핵심 내용 3문장.
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
            # Ensure we return a structured mock content even on exception
            return self.get_mock_ai_content()

    def get_mock_ai_content(self):
        """Fallback mock data matching the new structure"""
        return {
            "catchy_title": "🔥 'AI 거품론' 잠재운 독보적 실적... 엔비디아, 다시 한번 시장의 운명을 가르다",
            "core_summary": [
                "미국 증시는 빅테크 실적 기대감과 견조한 고용 지표에 힘입어 3대 지수 모두 상승 마감했습니다.",
                "특히 반도체 섹터의 강세가 돋보였으며, 금리 하락 안정화가 기술주에 우호적인 환경을 조성했습니다.",
                "지정학적 리스크에도 불구하고 시장의 시선은 실물 지표와 기업 이익으로 집중되는 모습입니다."
            ],
            "sections": [
                {
                    "emoji_tag": "🚀",
                    "title": "끝나지 않는 AI 랠리, 중심에는 여전히 엔비디아가 있다",
                    "content": "최근 일각에서 제기된 AI 과잉 투자 우려를 불식시키듯, 엔비디아를 비롯한 반도체 밸류체인 전반에 강력한 매수세가 유입되었어요. 블랙웰 아키텍처의 본격적인 양산 소식과 함께 데이터센터 수요가 여전히 견조하다는 점이 증명되면서 투자자들의 의구심은 확신으로 변하고 있습니다. 단순한 기대감을 넘어 실질적인 매출 지표가 뒷받침되고 있다는 점이 이번 랠리의 핵심입니다."
                },
                {
                    "emoji_tag": "🙏",
                    "title": "연준의 입과는 다른 시장의 길, '골디락스' 기대감 확산",
                    "content": "연준 위원들의 매파적 발언이 이따금 시장을 흔들기도 하지만, 현재 시장은 '너무 뜨겁지도 차갑지도 않은' 골디락스 국면에 주목하고 있어요. 고용 시장은 탄탄하게 버텨주면서도 인플레이션 압력은 서서히 낮아지는 지표들이 나오면서, 경기 침체 없는 금리 인하 시나리오가 현실화될 가능성이 커지고 있습니다. 이는 국채 금리 안정화로 이어져 밸류에이션 부담이 컸던 소형 성장주들에게도 숨통을 틔워주고 있어요."
                },
                {
                    "emoji_tag": "⚠️",
                    "title": "지정학적 변수와 관세 전쟁의 서막, 긴장 늦출 수 없어",
                    "content": "트럼프 정부의 관세 정책이 구체화되면서 글로벌 공급망 재편에 대한 우려가 다시 고개를 들고 있습니다. 특히 유럽과의 무역 갈등이 표면화될 경우, 글로벌 매출 비중이 높은 대형 기술주들에게는 비용 상승 압박으로 작용할 수 있어요. 지정학적 리스크는 단기 변동성을 키우는 요인이지만, 장기적으로는 공급망의 로컬화와 자동화 투자를 가속화시키는 촉매제가 될 수도 있다는 분석이 나옵니다."
                }
            ],
            "hashtags": ["#엔비디아", "#AI반도체", "#미국증시", "#골디락스", "#관세전쟁", "#나스닥"],
            "market_mood_narrative": "불확실성 속에서도 강력한 펀더멘털을 확인한 하루였습니다."
        }

    def generate_html(self, raw_data, ai_content):
        """Generate final premium HTML matching the user's blog style"""
        today_date = datetime.now().strftime("%Y.%m.%d")
        
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
        tags_html = " ".join([f'<span class="hashtag">{t}</span>' for t in ai_content.get('hashtags', [])])

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
        
        .container {{ 
            max-width: 800px; 
            margin: 0 auto; 
            background: var(--card-bg); 
            padding: 40px; 
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        .category {{ color: var(--brand-blue); font-weight: 800; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }}
        h1 {{ font-size: 28px; line-height: 1.3; margin-bottom: 15px; letter-spacing: -0.5px; }}
        .date {{ color: var(--text-sub); font-size: 14px; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border-color); }}

        .box-summary {{ 
            background: rgba(0, 112, 243, 0.05); 
            border-radius: 12px; 
            padding: 24px; 
            margin-bottom: 40px; 
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

        .article-section {{ margin-bottom: 50px; }}
        .section-header {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 15px; }}
        .emoji {{ font-size: 24px; }}
        .section-header h2 {{ font-size: 20px; font-weight: 800; line-height: 1.4; }}
        .section-content p {{ font-size: 16px; color: var(--text-main); margin-bottom: 15px; line-height: 1.8; text-align: justify; }}

        .market-brief {{ border-top: 2px solid var(--border-color); padding-top: 30px; margin-bottom: 40px; }}
        .brief-title {{ font-size: 18px; font-weight: 800; margin-bottom: 20px; }}
        .market-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border-color); font-size: 15px; }}
        .market-row .label {{ font-weight: 600; }}
        .market-row .val {{ font-family: 'JetBrains Mono', monospace; }}
        .market-row .chg.up {{ color: var(--brand-red); }}
        .market-row .chg.down {{ color: var(--brand-blue); }}

        .hashtags {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border-color); }}
        .hashtag {{ color: var(--text-sub); font-size: 14px; margin-right: 15px; }}

        .footer {{ margin-top: 60px; text-align: center; font-size: 12px; color: var(--text-sub); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="category">Daily Morning Report</div>
        <h1>{ai_content['catchy_title']}</h1>
        <div class="date">{today_date} • Premium AI Analysis</div>

        <div class="box-summary">
            <h3>핵심 요약</h3>
            <ul>
                { "".join([f'<li>{line}</li>' for line in ai_content['core_summary']]) }
            </ul>
        </div>

        <div class="market-brief">
            <div class="brief-title">미국 증시는 어땠어? {raw_data['date']} 장마감</div>
            <div class="market-indices">
                {indices_html}
            </div>
        </div>

        {sections_html}

        <div class="market-brief">
            <div class="brief-title">원자재 및 가상자산 현황</div>
            {comm_items}
        </div>

        <div class="hashtags">
            {tags_html}
        </div>

        <div class="footer">
            <p>© 2026 US Market AI Analyst • Powered by Gemini 1.5 Flash</p>
        </div>
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
    USDailyReportGenerator(data_dir='us_market').run()
