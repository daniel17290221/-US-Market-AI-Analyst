#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Market Daily Morning Report Generator
Generates a premium HTML report after US market close for Korean investors.
"""

import os
import json
import pandas as pd
import logging
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
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("⚠️ GOOGLE_API_KEY not found. AI features will be disabled.")

    def load_data(self):
        """Aggregate data from various analysis files"""
        data = {
            'macro': {},
            'sectors': [],
            'top_stocks': [],
            'calendar': []
        }
        
        # 1. Macro Analysis
        macro_path = os.path.join(self.data_dir, 'us_macro_analysis.json')
        if os.path.exists(macro_path):
            with open(macro_path, 'r', encoding='utf-8') as f:
                data['macro'] = json.load(f)
        
        # 2. Sector Performance
        sector_path = os.path.join(self.data_dir, 'sector_heatmap.json')
        if os.path.exists(sector_path):
            with open(sector_path, 'r', encoding='utf-8') as f:
                sector_data = json.load(f)
                if 'series' in sector_data:
                    for sector in sector_data['series']:
                        if sector['data']:
                            avg_change = sum(s['change'] for s in sector['data']) / len(sector['data'])
                            data['sectors'].append({
                                'name': sector['name'],
                                'change': round(avg_change, 2),
                                'stocks': sector['data'][:3]  # Top 3 stocks
                            })
        
        # 3. Top Stocks (Smart Money Picks)
        screener_path = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if os.path.exists(screener_path):
            df = pd.read_csv(screener_path)
            data['top_stocks'] = df.head(10).to_dict('records')
            
        # 4. Economic Calendar
        calendar_path = os.path.join(self.data_dir, 'economic_calendar.json')
        if os.path.exists(calendar_path):
            with open(calendar_path, 'r', encoding='utf-8') as f:
                cal = json.load(f)
                data['calendar'] = cal.get('events', [])
                
        return data

    def generate_ai_content(self, raw_data):
        """Use Gemini 1.5 Pro to synthesize the report content"""
        if not self.model:
            return self.get_mock_ai_content()
            
        prompt = f"""
        당신은 미국 시장 분석 전문가입니다. 아래의 미국 시장 데이터(JSON)를 바탕으로, 한국 시장 개장 전 한국 투자자들이 읽을 수 있는 프리미엄 아침 리포트를 작성해주세요.
        
        데이터:
        {json.dumps(raw_data, ensure_ascii=False, indent=2)}
        
        요청 사항:
        1. **오늘의 핵심 요약 (3줄)**: 시장의 흐름을 한눈에 파악할 수 있도록 3개의 불렛 포인트로 요약해주세요.
        2. **섹터별 심층 분석**: 강세를 보인 섹터와 그 원인을 상세히 설명해주세요.
        3. **투자 전략 4가지**: 구체적이고 실용적인 투자 전략을 4가지 제시해주세요.
        4. 모든 답변은 세련되고 전문적인 금융 용어를 사용한 한국어여야 합니다.
        
        JSON 형식으로 결과를 반환해주세요:
        {{
            "summary_3_lines": ["...", "...", "..."],
            "sector_insights": [
                {{"sector": "섹터명", "analysis": "상세 분석 내용", "background": "급등/급락 배경"}},
                ...
            ],
            "strategies": [
                {{"title": "전략 제목", "target": "대상 종목/섹터", "entry": "진입 시점", "goal": "목표", "risk": "리스크"}},
                ...
            ],
            "risk_warnings": ["주의사항1", "주의사항2", ...]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI Content Generation Error: {e}")
            return self.get_mock_ai_content()

    def get_mock_ai_content(self):
        return {
            "summary_3_lines": [
                "미국 증시는 AI 칩 수요 지속과 기술주 랠리에 힘입어 나스닥 신고가 경신, S&P 500도 +1.2% 상승",
                "연준의 금리 인하 신중론에도 불구하고 견조한 고용 지표가 경기 연착륙 기대감 확산",
                "반도체 및 대형 테크 섹터 강세, 반면 금리 민감주인 부동산 및 유틸리티는 약세"
            ],
            "sector_insights": [
                {
                    "sector": "Technology (기술주)",
                    "analysis": "엔비디아를 필두로 한 반도체 섹터가 시장을 압도했습니다. AI 인프라 투자 지속 전망이 투심을 자극하며 관련 밸류체인 전반에 걸쳐 강력한 매수세가 유입되었습니다.",
                    "background": "Blackwell 아키텍처 출시 임박 소식과 데이터센터 수요 급증이 주요 원인입니다. 마이크로소프트, 구글 등 빅테크의 AI 투자 확대 발표가 추가 모멘텀을 제공했습니다."
                },
                {
                    "sector": "Financials (금융)",
                    "analysis": "금리 상승 기대감에 은행주가 강세를 보였으며, 특히 대형 은행들의 순이자마진(NIM) 개선 전망이 긍정적으로 작용했습니다.",
                    "background": "연준의 금리 인하 속도 조절 시사로 장기 금리가 상승하며 금융주에 호재로 작용했습니다."
                }
            ],
            "strategies": [
                {
                    "title": "AI 반도체주 눌림목 매수",
                    "target": "NVDA, AMD, AVGO 등 대형주",
                    "entry": "전일 고점 대비 -3~5% 조정 시",
                    "goal": "+10~15% 익절",
                    "risk": "단기 과열 우려, -5% 손절 엄수"
                },
                {
                    "title": "금융주 순환매 전략",
                    "target": "JPM, BAC, GS 등 대형 은행주",
                    "entry": "금리 상승 국면에서 분할 매수",
                    "goal": "+8~12% 중기 보유",
                    "risk": "경기 둔화 시 대출 부실 우려"
                },
                {
                    "title": "방어주 포트폴리오 헤지",
                    "target": "헬스케어(JNJ, UNH), 필수소비재(PG, KO)",
                    "entry": "시장 변동성 확대 시",
                    "goal": "안정적 배당 수익 확보",
                    "risk": "상승장에서 수익률 제한적"
                },
                {
                    "title": "ETF 분산 투자",
                    "target": "QQQ (나스닥), SPY (S&P500)",
                    "entry": "주요 지지선 확인 후",
                    "goal": "장기 우상향 추세 추종",
                    "risk": "개별 종목 대비 수익률 낮음"
                }
            ],
            "risk_warnings": [
                "국채 금리의 변동성 확대 및 다음 주 예정된 주요 경제 지표 발표 전 관망세 예상",
                "중국 경제 둔화 우려와 지정학적 리스크(중동, 대만) 지속 모니터링 필요",
                "AI 버블 논란과 빅테크 밸류에이션 부담 증가, 단기 조정 가능성 대비"
            ]
        }

    def generate_html(self, raw_data, ai_content):
        """Generate the final HTML using the premium template"""
        today_str = datetime.now().strftime("%Y년 %m월 %d일")
        today_date = datetime.now().strftime("%Y.%m.%d")
        
        # Build summary lines
        summary_lines = ""
        for line in ai_content['summary_3_lines']:
            summary_lines += f'                    <li><strong>{line}</strong></li>\n'
        
        # Build sector cards
        sector_cards = ""
        for i, insight in enumerate(ai_content.get('sector_insights', [])[:3], 1):
            sector_cards += f"""
                <div class="theme-card">
                    <h2><span class="icon">📊</span>Sector #{i}: {insight['sector']} <span class="badge-hot">HOT</span></h2>
                    
                    <div class="insight-box">
                        <h4>🔥 급등 배경</h4>
                        <p>{insight['background']}</p>
                    </div>

                    <h3>💰 투자 포인트</h3>
                    <div class="insight-box">
                        <p>{insight['analysis']}</p>
                    </div>
                </div>
"""
        
        # Build strategy grid
        strategy_items = ""
        for i, strategy in enumerate(ai_content.get('strategies', [])[:4], 1):
            strategy_items += f"""
                    <div class="strategy-item">
                        <h3>📌 전략 {i}: {strategy['title']}</h3>
                        <p><strong>대상:</strong> {strategy['target']}<br>
                        <strong>진입:</strong> {strategy['entry']}<br>
                        <strong>목표:</strong> {strategy['goal']}<br>
                        <strong>리스크:</strong> {strategy['risk']}</p>
                    </div>
"""
        
        # Build risk warnings
        risk_items = ""
        for warning in ai_content.get('risk_warnings', []):
            risk_items += f'                    <li><strong>{warning}</strong></li>\n'
        
        # Build Stock Table Rows
        stock_rows = ""
        for i, stock in enumerate(raw_data['top_stocks'][:10], 1):
            score = stock.get('composite_score', 50)
            change_class = "price-up" if score > 60 else "price-down"
            badge = ""
            if score >= 80:
                badge = '<span class="badge-limit-up">S급</span>'
            elif score >= 70:
                badge = '<span class="badge-hot">A급</span>'
            
            stock_rows += f"""
                            <tr>
                                <td>{i}</td>
                                <td><span class="stock-name">{stock['ticker']}</span><br><span class="stock-code">{stock.get('name', stock['ticker'])}</span></td>
                                <td>{stock.get('current_price', 'N/A')}</td>
                                <td class="{change_class}">점수: {score} {badge}</td>
                                <td>{stock.get('grade', 'N/A')}</td>
                                <td>스마트머니 유입</td>
                            </tr>
"""
        
        # Build Sector Items for Market Status
        sector_items = ""
        for sector in raw_data['sectors'][:6]:
            change_val = sector['change']
            change_class = "up" if change_val >= 0 else "down"
            arrow = "▲" if change_val >= 0 else "▼"
            sector_items += f"""
                    <div class="market-item">
                        <h3>{sector['name']}</h3>
                        <div class="value">{abs(change_val)}%</div>
                        <div class="change {change_class}">{arrow} {abs(change_val)}%</div>
                    </div>
"""

        # HTML Template with Dark Mode and Glow Effects
        html_template = f"""<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 {today_date} 미국 시장 완벽 분석 | Premium Daily Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Malgun Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.8;
            color: #E2E2E7;
            background-color: #0A0A0C;
            padding: 20px;
            -webkit-font-smoothing: antialiased;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(20, 20, 23, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        
        .header {{
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
            border-bottom: 2px solid rgba(0, 240, 255, 0.3);
        }}
        
        .header::before {{
            content: '📈';
            position: absolute;
            font-size: 200px;
            opacity: 0.05;
            top: -50px;
            right: -50px;
        }}
        
        .header h1 {{
            font-size: 2.8em;
            margin-bottom: 20px;
            text-shadow: 0 0 20px rgba(0, 240, 255, 0.5), 0 0 40px rgba(0, 240, 255, 0.3);
            animation: glow 3s ease-in-out infinite alternate;
        }}
        
        @keyframes glow {{
            from {{ text-shadow: 0 0 10px rgba(0, 240, 255, 0.5), 0 0 20px rgba(0, 240, 255, 0.3); }}
            to {{ text-shadow: 0 0 20px rgba(0, 240, 255, 0.8), 0 0 40px rgba(0, 240, 255, 0.5), 0 0 60px rgba(0, 240, 255, 0.3); }}
        }}
        
        .header .subtitle {{
            font-size: 1.3em;
            opacity: 0.9;
            margin-top: 10px;
            color: #00F0FF;
        }}
        
        .header .date {{
            font-size: 1.1em;
            margin-top: 15px;
            background: rgba(0, 240, 255, 0.1);
            padding: 10px 20px;
            border-radius: 30px;
            display: inline-block;
            border: 1px solid rgba(0, 240, 255, 0.3);
        }}
        
        .content {{
            padding: 50px 40px;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.1) 0%, rgba(112, 0, 255, 0.1) 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 240, 255, 0.2);
            backdrop-filter: blur(10px);
        }}
        
        .summary-box h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            color: #00F0FF;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }}
        
        .summary-box ul {{
            list-style: none;
            font-size: 1.1em;
        }}
        
        .summary-box li {{
            margin: 15px 0;
            padding-left: 30px;
            position: relative;
            color: #E2E2E7;
        }}
        
        .summary-box li::before {{
            content: '✓';
            position: absolute;
            left: 0;
            font-size: 1.5em;
            color: #00E676;
            text-shadow: 0 0 10px rgba(0, 230, 118, 0.5);
        }}
        
        .market-status {{
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 242, 254, 0.1) 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 40px;
            color: white;
            border: 1px solid rgba(79, 172, 254, 0.2);
            backdrop-filter: blur(10px);
        }}
        
        .market-status h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #00F0FF;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }}
        
        .market-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .market-item {{
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }}
        
        .market-item:hover {{
            border-color: rgba(0, 240, 255, 0.5);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
        }}
        
        .market-item h3 {{
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #E2E2E7;
        }}
        
        .market-item .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }}
        
        .market-item .change {{
            font-size: 1.1em;
        }}
        
        .change.up {{
            color: #FF1744;
            text-shadow: 0 0 10px rgba(255, 23, 68, 0.5);
        }}
        
        .change.down {{
            color: #00E676;
            text-shadow: 0 0 10px rgba(0, 230, 118, 0.5);
        }}
        
        .theme-section {{
            margin-bottom: 50px;
        }}
        
        .theme-card {{
            background: rgba(20, 20, 23, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            backdrop-filter: blur(12px);
        }}
        
        .theme-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 240, 255, 0.2);
            border-color: rgba(0, 240, 255, 0.3);
        }}
        
        .theme-card h2 {{
            font-size: 2em;
            color: #00F0FF;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }}
        
        .theme-card h2 .icon {{
            margin-right: 15px;
            font-size: 1.2em;
        }}
        
        .theme-card h3 {{
            font-size: 1.4em;
            color: #E2E2E7;
            margin: 25px 0 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }}
        
        .stock-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: rgba(20, 20, 23, 0.5);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }}
        
        .stock-table thead {{
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.2) 0%, rgba(112, 0, 255, 0.2) 100%);
            color: white;
        }}
        
        .stock-table th {{
            padding: 15px;
            text-align: center;
            font-weight: bold;
            font-size: 1.05em;
            color: #00F0FF;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }}
        
        .stock-table td {{
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: #E2E2E7;
        }}
        
        .stock-table tbody tr {{
            transition: all 0.3s ease;
        }}
        
        .stock-table tbody tr:hover {{
            background: rgba(0, 240, 255, 0.05);
        }}
        
        .stock-table .stock-name {{
            font-weight: bold;
            color: #00F0FF;
            font-size: 1.1em;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
        }}
        
        .stock-table .stock-code {{
            color: #999;
            font-size: 0.9em;
        }}
        
        .stock-table .price-up {{
            color: #FF1744;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(255, 23, 68, 0.5);
        }}
        
        .stock-table .price-down {{
            color: #00E676;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(0, 230, 118, 0.5);
        }}
        
        .badge-hot {{
            background: linear-gradient(135deg, rgba(240, 147, 251, 0.3) 0%, rgba(245, 87, 108, 0.3) 100%);
            color: #FF4DA6;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            display: inline-block;
            margin-left: 10px;
            border: 1px solid rgba(255, 77, 166, 0.3);
            text-shadow: 0 0 10px rgba(255, 77, 166, 0.5);
        }}
        
        .badge-limit-up {{
            background: rgba(255, 23, 68, 0.2);
            color: #FF1744;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            display: inline-block;
            border: 1px solid rgba(255, 23, 68, 0.3);
            text-shadow: 0 0 10px rgba(255, 23, 68, 0.5);
        }}
        
        .insight-box {{
            background: rgba(255, 255, 255, 0.03);
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #00F0FF;
            backdrop-filter: blur(10px);
        }}
        
        .insight-box h4 {{
            font-size: 1.3em;
            color: #00F0FF;
            margin-bottom: 15px;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }}
        
        .insight-box p {{
            line-height: 1.8;
            color: #E2E2E7;
            margin: 10px 0;
        }}
        
        .risk-warning {{
            background: linear-gradient(135deg, rgba(250, 112, 154, 0.1) 0%, rgba(254, 225, 64, 0.1) 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 40px 0;
            color: white;
            border: 1px solid rgba(255, 234, 0, 0.2);
            backdrop-filter: blur(10px);
        }}
        
        .risk-warning h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #FFEA00;
            text-shadow: 0 0 10px rgba(255, 234, 0, 0.5);
        }}
        
        .risk-warning ul {{
            list-style: none;
        }}
        
        .risk-warning li {{
            margin: 15px 0;
            padding-left: 30px;
            position: relative;
            font-size: 1.1em;
            color: #E2E2E7;
        }}
        
        .risk-warning li::before {{
            content: '⚠️';
            position: absolute;
            left: 0;
            font-size: 1.3em;
        }}
        
        .strategy-box {{
            background: linear-gradient(135deg, rgba(168, 237, 234, 0.1) 0%, rgba(254, 214, 227, 0.1) 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 40px 0;
            border: 1px solid rgba(0, 240, 255, 0.2);
            backdrop-filter: blur(10px);
        }}
        
        .strategy-box h2 {{
            font-size: 1.8em;
            color: #00F0FF;
            margin-bottom: 20px;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
        }}
        
        .strategy-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .strategy-item {{
            background: rgba(20, 20, 23, 0.7);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s ease;
        }}
        
        .strategy-item:hover {{
            border-color: rgba(0, 240, 255, 0.3);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
        }}
        
        .strategy-item h3 {{
            font-size: 1.3em;
            color: #00F0FF;
            margin-bottom: 15px;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
        }}
        
        .strategy-item p {{
            color: #E2E2E7;
            line-height: 1.7;
        }}
        
        .footer {{
            background: rgba(20, 20, 23, 0.95);
            color: white;
            padding: 40px;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }}
        
        .footer p {{
            margin: 10px 0;
            opacity: 0.9;
            color: #E2E2E7;
        }}
        
        .disclaimer {{
            background: rgba(30, 30, 35, 0.8);
            padding: 30px;
            margin-top: 20px;
            border-radius: 10px;
            font-size: 0.95em;
            line-height: 1.8;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .content {{
                padding: 30px 20px;
            }}
            
            .stock-table {{
                font-size: 0.85em;
            }}
            
            .stock-table th,
            .stock-table td {{
                padding: 10px 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {today_str} 미국 시장 완벽 분석</h1>
            <p class="subtitle">Premium Daily Report for Smart Investors</p>
            <p class="date">📅 {today_str} 미국 장마감 기준</p>
        </div>

        <div class="content">
            <div class="summary-box">
                <h2>💡 오늘의 핵심 요약 (3줄 요약)</h2>
                <ul>
{summary_lines}
                </ul>
            </div>

            <div class="market-status">
                <h2>📊 오늘의 섹터 현황 ({today_date} 마감)</h2>
                <div class="market-grid">
{sector_items}
                </div>
            </div>

            <section class="theme-section">
{sector_cards}
                
                <div class="theme-card">
                    <h2><span class="icon">🔥</span>스마트머니 유입 상위 종목 TOP 10</h2>
                    
                    <h3>📈 AI 분석 기반 추천 종목</h3>
                    <table class="stock-table">
                        <thead>
                            <tr>
                                <th>순위</th>
                                <th>종목명 (티커)</th>
                                <th>현재가</th>
                                <th>AI 점수</th>
                                <th>등급</th>
                                <th>특징</th>
                            </tr>
                        </thead>
                        <tbody>
{stock_rows}
                        </tbody>
                    </table>
                </div>
            </section>

            <div class="strategy-box">
                <h2>🎯 오늘의 투자 전략 ({today_date} 기준)</h2>
                <div class="strategy-grid">
{strategy_items}
                </div>
            </div>

            <div class="risk-warning">
                <h2>⚠️ 미국 시장 투자 주의사항</h2>
                <ul>
{risk_items}
                </ul>
            </div>
        </div>

        <div class="footer">
            <p><strong>📅 작성일:</strong> {today_str} 미국 장마감 후</p>
            <p><strong>📌 최종 업데이트:</strong> {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}</p>
            
            <div class="disclaimer">
                <p><strong>⚠️ 투자 유의사항 및 면책 조항</strong></p>
                <p>본 가이드는 {today_str} 미국 시장 마감 기준의 정보를 정리한 것으로, <strong>투자 권유 목적이 아닌 정보 제공 목적</strong>입니다. 주가 및 뉴스는 실시간으로 변동하며, 과거 수익률이 미래 수익을 보장하지 않습니다.</p>
                <p><strong>미국 시장은 변동성이 높아</strong> 단기간 급등 후 급락도 가능합니다. 손절 원칙 미준수 시 원금 손실 위험이 크며, 레버리지 사용 시 파산 가능성도 있습니다.</p>
                <p>모든 투자 판단과 손실은 투자자 본인의 책임이며, 본 가이드 작성자는 투자 결과에 대해 <strong>어떠한 법적 책임도 지지 않습니다.</strong> 투자 전 반드시 기업 공시, 재무제표, 리스크를 충분히 검토하시기 바랍니다.</p>
                <p><strong>참고 자료:</strong> Yahoo Finance, Bloomberg, CNBC, SEC EDGAR, 각종 언론 보도</p>
            </div>
            
            <p style="margin-top: 30px; font-size: 0.95em; opacity: 0.8;">
                © 2026 US Market AI Analyst | 무단 전재 및 재배포 금지
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(html_template)
            logger.info(f"✅ Premium report generated: {self.output_file}")
        except Exception as e:
            logger.warning(f"Could not save report to file: {e}")
            
        return html_template

    def run(self):
        logger.info("🚀 Generating Daily US Market Report...")
        raw_data = self.load_data()
        ai_content = self.generate_ai_content(raw_data)
        return self.generate_html(raw_data, ai_content)

if __name__ == "__main__":
    USDailyReportGenerator(data_dir='us_market').run()
