import os
import json
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRDailyReportGenerator:
    def __init__(self, data_dir='kr_market', output_file='kr_market_daily_report.html'):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("google_api_key")
        if not self.api_key:
            logger.error("❌ GOOGLE_API_KEY not found in environment variables.")
        
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, 'kr_daily_data.json')
        self.output_file = os.path.join(data_dir, output_file)

    def load_data(self):
        try:
            if not os.path.exists(self.data_file):
                logger.warning(f"⚠️ KR data file not found at {self.data_file}")
                return None
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading KR data: {e}")
            return None

    def generate_ai_content(self, raw_data):
        logger.info("🤖 Generating KR AI Content with Gemini REST API...")
        
        if not self.api_key:
            return self.get_fallback_content()

        # Prepare stock data context for AI
        stocks_context = ""
        for s in raw_data.get('top_stocks', []):
            stocks_context += f"- {s['name']}({s['symbol']}): {s['price']}원 ({s['change']})\n"

        prompt = f"""
        당신은 대한민국 증시 전문 시황 분석가 'VibeCodingLab KR'입니다.
        아래의 실시간 국내 증시 데이터를 바탕으로 투자자들이 아침에 읽기 좋은 프리미엄 '국내 증시 마감 리포트'를 작성해주세요.

        [시장 데이터]
        날짜: {raw_data['date']}
        지수 현황: {json.dumps(raw_data['market_indices'], ensure_ascii=False)}
        주요 종목 시황: 
        {stocks_context}
        환율 및 원자재: {json.dumps(raw_data['commodities'], ensure_ascii=False)}
        수급 현황(외인/기관): {json.dumps(raw_data.get('investor_flows', {}), ensure_ascii=False)}
        주요 뉴스: {json.dumps(raw_data.get('market_news', [])[:5], ensure_ascii=False)}

        [작성 지침]
        1. **헤드라인**: 독자의 시선을 사로잡는 섹시하고 통찰력 있는 헤드라인을 뽑아주세요.
        2. **핵심 요약**: 오늘 시장을 관통하는 3가지 핵심 포인트를 작성해주세요.
        3. **상세 분석 섹션 (3개 이상)**: 
           - '마켓 드라이버': 오늘 지수 등락의 결정적 원인 (수급, 대외 변수 등)
           - '섹터 이슈': 주도 섹터 및 소외 섹터의 원인과 결과
           - '내일의 관전 포인트': 다음 거래일의 핵심 대응 전략
        4. **말투**: 전문적이고 분석적이며, 신뢰감 있는 언론사 뉴스 스타일(예: 한국경제, 매일경제)로 작성해주세요.
        5. **형식**: 반드시 아래 JSON 형식을 엄격히 지켜주세요. JSON 외의 텍스트는 포함하지 마세요.

        [JSON 출력 형식]
        {{
            "catchy_title": "헤드라인 문구",
            "core_summary": ["요약1", "요약2", "요약3"],
            "sections": [
                {{
                    "title": "섹션 제목",
                    "emoji_tag": "📌",
                    "content": "상세 분석 내용 (최소 3문장 이상 풍성하게)"
                }}
            ],
            "hashtags": ["#코스피", "#삼성전자", "#국내증시"]
        }}
        """

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.7
                }
            }
            
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                res_json = resp.json()
                content_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                return json.loads(content_text)
            else:
                logger.error(f"❌ AI API Error: {resp.status_code} - {resp.text}")
                return self.get_fallback_content()
        except Exception as e:
            logger.error(f"❌ AI Generation Error: {e}")
            return self.get_fallback_content()

    def generate_html(self, raw_data, ai_content):
        try:
            import pytz
            kst = pytz.timezone('Asia/Seoul')
            kst_now = datetime.now(kst)
        except ImportError:
            # Fallback if pytz is not available
            kst_now = datetime.utcnow() + timedelta(hours=9)
            
        today_date = kst_now.strftime("%Y.%m.%d")
        gen_time = kst_now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Build Index Cards
        indices_html = ""
        for k, v in raw_data['market_indices'].items():
            is_up = '+' in v['change']
            change_class = 'up' if is_up else 'down'
            indices_html += f"""
            <div class="index-card">
                <div class="index-name">📈 {v['name']}</div>
                <div class="index-value">{v['price']}</div>
                <div class="index-change {change_class}">{v['change']}</div>
            </div>"""

        # Build Investor Flows
        flows_html = ""
        if 'investor_flows' in raw_data:
            for market, flows in raw_data['investor_flows'].items():
                flow_items = ""
                for flow in flows:
                    status_class = 'up' if flow['status'] == '매수' else ('down' if flow['status'] == '매도' else '')
                    flow_items += f"""
                    <div class="flow-item">
                        <span class="flow-label">{flow['label']}</span>
                        <span class="flow-value {status_class}">{flow['value']}</span>
                    </div>"""
                
                flows_html += f"""
                <div class="market-flow-card">
                    <div class="flow-market-name">{market} 수급</div>
                    <div class="flow-grid">{flow_items}</div>
                </div>"""

        # Build Market News
        news_html = ""
        if 'market_news' in raw_data:
            for item in raw_data['market_news'][:5]:
                news_html += f"""
                <a href="{item['url']}" target="_blank" class="news-list-item">
                    <div class="news-title-row">
                        <span class="news-source">{item['source']}</span>
                        <span class="news-title">{item['title']}</span>
                    </div>
                </a>"""

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
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4995156883730033" crossorigin="anonymous"></script>
    <style>
        :root {{
            --bg-color: #050505;
            --card-bg: #111111;
            --text-main: #e5e7eb;
            --text-sub: #9ca3af;
            --brand-blue: #00F0FF;
            --brand-red: #ff4d4f;
            --border-color: #333333;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: var(--bg-color); color: var(--text-main); font-family: 'Pretendard', sans-serif; line-height: 1.6; padding: 20px; }}
        .wrapper {{ 
            display: grid; 
            grid-template-columns: 180px minmax(600px, 1000px) 180px; 
            justify-content: center; 
            gap: 20px; 
            max-width: 1400px; 
            margin: 0 auto; 
            opacity: 0; 
            animation: fadeIn 0.5s ease-in-out forwards; 
        }}
        .ad-sidebar {{ width: 180px; display: flex; flex-direction: column; gap: 20px; position: sticky; top: 20px; height: fit-content; align-self: flex-start; }}
        .ad-unit {{ background: transparent; border: none; height: 600px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: var(--text-sub); font-size: 11px; padding: 15px; overflow: hidden; }}
        .container {{ max-width: 1000px; width: 100%; background: var(--card-bg); padding: 50px; border-radius: 12px; border: 1px solid var(--border-color); box-shadow: 0 4px 20px rgba(0,0,0,0.3); overflow: hidden; }}
        h1 {{ font-size: 32px; margin-bottom: 20px; letter-spacing: -1px; }}
        .date {{ color: var(--text-sub); margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border-color); }}
        .box-summary {{ background: rgba(0, 112, 243, 0.05); border-radius: 12px; padding: 25px; margin-bottom: 40px; border: 1px solid rgba(0, 112, 243, 0.1); }}
        .market-indices {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 25px; }}
        .index-card {{ padding: 15px; background: rgba(128,128,128,0.05); border-radius: 10px; text-align: center; border: 1px solid var(--border-color); }}
        .index-change.up {{ color: var(--brand-red); }}
        .index-change.down {{ color: var(--brand-blue); }}
        
        .investor-flows {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 40px; }}
        .market-flow-card {{ background: rgba(255,255,255,0.02); border-radius: 10px; padding: 15px; border: 1px solid var(--border-color); }}
        .flow-market-name {{ font-size: 13px; font-weight: bold; color: var(--brand-blue); margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid var(--border-color); }}
        .flow-grid {{ display: flex; justify-content: space-around; gap: 10px; }}
        .flow-item {{ display: flex; flex-direction: column; align-items: center; }}
        .flow-label {{ font-size: 11px; color: var(--text-sub); }}
        .flow-value {{ font-size: 14px; font-weight: bold; }}
        .flow-value.up {{ color: var(--brand-red); }}
        .flow-value.down {{ color: var(--brand-blue); }}

        .news-box {{ background: rgba(128,128,128,0.03); border-radius: 10px; padding: 20px; border: 1px solid var(--border-color); margin-bottom: 40px; }}
        .news-box h3 {{ font-size: 16px; margin-bottom: 15px; color: var(--brand-blue); display: flex; align-items: center; gap: 8px; }}
        .news-list-item {{ display: block; text-decoration: none; color: var(--text-main); padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s; }}
        .news-list-item:hover {{ background: rgba(255,255,255,0.02); }}
        .news-list-item:last-child {{ border-bottom: none; }}
        .news-source {{ font-size: 10px; background: var(--brand-blue); color: #000; padding: 1px 5px; border-radius: 3px; font-weight: bold; margin-right: 10px; }}
        .news-title {{ font-size: 14px; }}

        .article-section {{ margin-bottom: 50px; }}
        .section-header {{ display: flex; gap: 10px; margin-bottom: 15px; align-items: center; }}
        .footer {{ margin-top: 50px; text-align: center; font-size: 12px; color: var(--text-sub); border-top: 1px solid var(--border-color); padding-top: 20px; }}
        .ad-banner-bottom {{ 
            position: fixed; 
            bottom: 0; 
            left: 0; 
            width: 100%; 
            background: rgba(0, 0, 0, 0.8); 
            border-top: 1px solid var(--border-color); 
            padding: 10px; 
            text-align: center; 
            z-index: 1000; 
            backdrop-filter: blur(8px);
        }}
        @media (max-width: 1200px) {{ .ad-sidebar {{ display: none; }} body {{ padding-bottom: 120px; }} .container {{ min-width: 100%; }} .investor-flows {{ grid-template-columns: 1fr; }} }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body>
    <div class="wrapper">
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
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 40px; height: 40px; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 1px solid #333333; background: white; border-radius: 8px;">
                        <img src="/assets/logo.jpg" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div style="font-family: 'Pretendard', sans-serif;">
                        <span style="font-size: 18px; font-weight: 800; color: var(--text-main); font-style: italic;">Vibe<span style="color: var(--brand-blue);">CodingLab</span></span>
                    </div>
                </div>
                <span style="background: red; color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px;">🔴 KR MARKET LIVE: {gen_time}</span>
            </div>
            <h1>{ai_content['catchy_title']}</h1>
            <div class="date">{today_date} • VibeCodingLab KR Premium Analysis</div>
            <div class="box-summary"><h3>오늘의 3요약</h3><ul>{"".join([f'<li>{l}</li>' for l in ai_content['core_summary']])}</ul></div>
            <div class="market-indices">{indices_html}</div>
            
            <div class="investor-flows">{flows_html}</div>
            
            <div class="news-box">
                <h3>📰 주요 시장 헤드라인</h3>
                {news_html}
            </div>

            {sections_html}
            <div class="footer">
                © 2026 VibeCodingLab KR. All Rights Reserved.
            </div>
        </div>

        <aside class="ad-sidebar">
            <div class="ad-unit">
                <!-- 바이브코딩랩 KR 데일리 리포트 우측 -->
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
        <!-- 바이브코딩랩 KR 데일리 리포트 하단 전면 -->
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
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(html_template)
            logger.info(f"[SUCCESS] KR Premium report saved to: {self.output_file}")
        except Exception as e:
            logger.warning(f"[WARNING] Could not write KR report to filesystem: {e}")
            
        return html_template

    def get_fallback_content(self):
        return {
            "catchy_title": "코스피, 방향성 탐색 구간 진입",
            "core_summary": ["불확실성 상존", "외인 수급 관망", "개별 종목 장세"],
            "sections": [{"title": "시장 총평", "emoji_tag": "📌", "content": "데이터 수집 중입니다."}],
            "hashtags": ["#코스피", "#국내증시"]
        }

    def run(self):
        logger.info("Starting KR Market Daily Report Generation...")
        raw_data = self.load_data()
        if not raw_data: return
        ai_content = self.generate_ai_content(raw_data)
        self.generate_html(raw_data, ai_content)

if __name__ == "__main__":
    KRDailyReportGenerator().run()
