import os
import json
import logging
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRDailyReportGenerator:
    def __init__(self, data_dir='kr_market', output_file='kr_market_daily_report.html'):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("❌ GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, 'kr_daily_data.json')
        self.output_file = os.path.join(data_dir, output_file)

    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading KR data: {e}")
            return None

    def generate_ai_content(self, raw_data):
        logger.info("🤖 Generating KR AI Content with Gemini...")
        
        prompt = f"""
        당신은 대한민국 증시 전문 시황 분석가 'VibeCodingLab KR'입니다.
        아래의 실시간 국내 증시 데이터를 바탕으로 투자자들이 아침에 읽기 좋은 프리미엄 '국내 증시 마감 리포트'를 작성해주세요.

        [데이터]
        날짜: {raw_data['date']}
        지수 현황: {json.dumps(raw_data['market_indices'], ensure_ascii=False)}
        주요 종목 시황: {json.dumps(raw_data['top_stocks'], ensure_ascii=False)}
        환율 및 원자재: {json.dumps(raw_data['commodities'], ensure_ascii=False)}

        [작성 지침]
        1. 독자의 시선을 사로잡는 섹시한 헤드라인을 뽑아주세요.
        2. '핵심 요약' 3줄을 작성해주세요. (리스트 형식)
        3. '오늘의 코스피/코스닥' 섹션에서 지수의 움직임과 특징을 분석해주세요. (외인/기관 수급 언급 포함)
        4. '주도주 분석' 섹션에서 시총 상위 종목들의 특징적인 움직임을 설명해주세요.
        5. '투자 전략' 섹션에서 내일의 대응 전략을 제안해주세요.
        6. 말투는 신뢰감 있고 전문적인 언론사 뉴스 스타일로 작성해주세요.
        7. 결과는 반드시 아래 JSON 형식을 엄격히 지켜주세요.

        [JSON 출력 형식]
        {{
            "catchy_title": "헤드라인 문구",
            "core_summary": ["요약1", "요약2", "요약3"],
            "sections": [
                {{
                    "title": "섹션 제목",
                    "emoji_tag": "📌",
                    "content": "상세 분석 내용"
                }}
            ],
            "hashtags": ["#코스피", "#삼성전자", "#국내증시"]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            content_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(content_text)
        except Exception as e:
            logger.error(f"❌ AI Generation Error: {e}")
            return self.get_fallback_content()

    def generate_html(self, raw_data, ai_content):
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

        # Build Commodity Table
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
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --text-main: #e6edf3;
            --text-sub: #8b949e;
            --brand-blue: #58a6ff;
            --brand-red: #ff7b72;
            --border-color: #30363d;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: var(--bg-color); color: var(--text-main); font-family: 'Pretendard', sans-serif; line-height: 1.6; padding: 20px; }}
        .wrapper {{ display: flex; justify-content: center; gap: 20px; max-width: 1400px; margin: 0 auto; }}
        .ad-sidebar {{ width: 180px; flex-shrink: 0; display: flex; flex-direction: column; gap: 20px; position: sticky; top: 20px; height: fit-content; align-self: flex-start; }}
        .ad-unit {{ background: var(--card-bg); border: 2px dashed var(--border-color); border-radius: 12px; height: 600px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: var(--text-sub); font-size: 11px; padding: 15px; }}
        .container {{ max-width: 1000px; width: 100%; background: var(--card-bg); padding: 50px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
        h1 {{ font-size: 32px; margin-bottom: 20px; letter-spacing: -1px; }}
        .date {{ color: var(--text-sub); margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border-color); }}
        .box-summary {{ background: rgba(0, 112, 243, 0.05); border-radius: 12px; padding: 25px; margin-bottom: 40px; border: 1px solid rgba(0, 112, 243, 0.1); }}
        .market-indices {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 40px; }}
        .index-card {{ padding: 15px; background: rgba(128,128,128,0.05); border-radius: 10px; text-align: center; border: 1px solid var(--border-color); }}
        .index-change.up {{ color: var(--brand-red); }}
        .index-change.down {{ color: var(--brand-blue); }}
        .article-section {{ margin-bottom: 50px; }}
        .section-header {{ display: flex; gap: 10px; margin-bottom: 15px; align-items: center; }}
        .footer {{ margin-top: 50px; text-align: center; font-size: 12px; color: var(--text-sub); border-top: 1px solid var(--border-color); padding-top: 20px; }}
        .mobile-ad-banner {{ display: none; position: fixed; bottom: 0; left: 0; width: 100%; background: #fff; border-top: 1px solid #eee; padding: 10px; text-align: center; z-index: 1000; }}
        @media (max-width: 1200px) {{ .ad-sidebar {{ display: none; }} .mobile-ad-banner {{ display: block; }} body {{ padding-bottom: 100px; }} }}
    </style>
</head>
<body>
    <div class="wrapper">
        <aside class="ad-sidebar">
            <div class="ad-unit">
                <script src="https://ads-partners.coupang.com/g.js"></script>
                <script>new PartnersCoupang.G({{ "id":961293,"template":"carousel","trackingCode":"AF1993837","width":"180","height":"600" }});</script>
            </div>
        </aside>

        <div class="container">
            <div style="text-align: right; margin-bottom: 20px;"><span style="background: red; color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px;">🔴 KR MARKET LIVE: {gen_time}</span></div>
            <h1>{ai_content['catchy_title']}</h1>
            <div class="date">{today_date} • VibeCodingLab KR Premium Analysis</div>
            <div class="box-summary"><h3>오늘의 3요약</h3><ul>{"".join([f'<li>{l}</li>' for l in ai_content['core_summary']])}</ul></div>
            <div class="market-indices">{indices_html}</div>
            {sections_html}
            <div class="footer">
                <div style="margin-bottom: 10px;">"이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."</div>
                © 2026 VibeCodingLab KR. All Rights Reserved.
            </div>
        </div>

        <aside class="ad-sidebar">
            <div class="ad-unit">
                <script src="https://ads-partners.coupang.com/g.js"></script>
                <script>new PartnersCoupang.G({{ "id":961294,"template":"carousel","trackingCode":"AF1993837","width":"180","height":"600" }});</script>
            </div>
        </aside>
    </div>
    <div class="mobile-ad-banner">
        <script src="https://ads-partners.coupang.com/g.js"></script>
        <script>new PartnersCoupang.G({{ "id":961291,"template":"carousel","trackingCode":"AF1993837","width":"320","height":"100" }});</script>
    </div>
</body>
</html>
        """
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        logger.info(f"✅ KR Premium report saved to: {self.output_file}")
        return html_template

    def get_fallback_content(self):
        return {
            "catchy_title": "코스피, 방향성 탐색 구간 진입",
            "core_summary": ["불확실성 상존", "외인 수급 관망", "개별 종목 장세"],
            "sections": [{"title": "시장 총평", "emoji_tag": "📌", "content": "데이터 수집 중입니다."}],
            "hashtags": ["#코스피", "#국내증시"]
        }

    def run(self):
        logger.info("🚀 Starting KR Market Daily Report Generation...")
        raw_data = self.load_data()
        if not raw_data: return
        ai_content = self.generate_ai_content(raw_data)
        self.generate_html(raw_data, ai_content)

if __name__ == "__main__":
    KRDailyReportGenerator().run()
