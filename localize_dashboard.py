
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Translate Headers & Navigation
    html = html.replace('Market Analysis', '시장 분석').replace('Calendar', '경제 일정').replace('Historical', '과거 패턴')
    html = html.replace('US Market <span class="text-brand-primary">AI Terminal</span>', '미국 시장 <span class="text-brand-primary">AI 분석 터미널</span>')
    
    # 2. Main Analysis Section
    html = html.replace('점수:', 'AI 점수:').replace('점수: 96 / 100', 'AI 점수: 96 / 100')
    html = html.replace('Market Cap', '시가 총액').replace('Vol Ratio', '거래량 비율').replace('Strength', '신호 강도')
    html = html.replace('AI Investment Insight', 'AI 투자 분석 인사이트').replace('Risk Factors', '핵심 리스크 요인')
    html = html.replace('+0% Potential Upside', '+0% 예상 상승 여력')
    html = html.replace('Valuation Spectrum', '적정 주가 분석 (DCF)').replace('DCF Target Model', 'AI 적정가 모델')
    html = html.replace('SWOT Strength', '강점 (S)').replace('SWOT Weakness', '약점 (W)').replace('SWOT Opportunity', '기회 (O)').replace('SWOT Threats', '위협 (T)')

    # 3. Smart Money Table
    html = html.replace('Real-time Smart Money <span class="text-gray-500 font-medium">Top 10 Picks</span>', '실시간 스마트 머니 <span class="text-gray-500 font-medium">Top 10 추천주</span>')
    html = html.replace('RANK', '순위').replace('TICKER', '티커').replace('SECTOR', '섹터').replace('AI SCORE', 'AI 점수').replace('STATUS', '분석 상태').replace('PRICE', '현재가').replace('CHANGE', '등락율')

    # 4. Sidebar Widgets
    html = html.replace('Market Sector Flow', '시장 섹터 맵 (S&P 500)')
    html = html.replace('AI Macro Outlook', 'AI 거시 경제 전망').replace('Sentiment Index', '시장 심리 지수').replace('Key Findings', '핵심 분석 결과')
    html = html.replace('Market Events', '주요 경제 일정').replace('ETF Flow Monitor', 'ETF 자금 흐름 모니터')

    # 5. Restore Heatmap Widget (Replacing Hotlists with Heatmap)
    heatmap_widget = """
                                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
                                {
                                  "exchanges": [],
                                  "dataSource": "S&P500",
                                  "grouping": "sector",
                                  "blockSize": "market_cap_basic",
                                  "blockColor": "change",
                                  "locale": "kr",
                                  "symbolUrl": "",
                                  "colorTheme": "dark",
                                  "hasTopBar": false,
                                  "isTransparent": true,
                                  "hasSymbolTooltip": true,
                                  "width": "100%",
                                  "height": "100%"
                                }
                                </script>
    """
    # Replace the hotlists script with heatmap script
    html = re.sub(r'<script type="text/javascript" src="https://s3\.tradingview\.com/external-embedding/embed-widget-hotlists\.js"[\s\S]*?</script>', heatmap_widget, html)

    # 6. Translate JavaScript Strings
    html = html.replace('UP Potential', '상승 여력')
    html = html.replace('NO DATA FLOW DETECTED', '데이터를 불러오는 중입니다...')
    html = html.replace('Synchronizing Flows...', '데이터 동기화 중...')
    html = html.replace('NO FLOW DATA', '동기화된 데이터 없음')
    html = html.replace('Inflow', '유입').replace('Outflow', '유출')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("SUCCESS: Full Localization and Heatmap Restoration completed.")

except Exception as e:
    print(f"ERROR: {e}")
