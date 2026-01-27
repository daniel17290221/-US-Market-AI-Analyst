
import os

# Define the intended Korean strings that got corrupted
korean_replacements = {
    "ë¯¸êµ­ ì‹œìž¥ ëŒ€ì‹œë³´ë“œ": "미국 시장 대시보드",
    "ë °ì ¼ë¦¬ ë¶„ì„  ë¦¬í ¬íŠ¸": "데일리 분석 리포트",
    "ê²½ì œ ìº˜ë¦°ë ”": "경제 캘린더",
    "ì „ì²´ ë¶„ì„ ": "전체 분석",
    "ìƒ ì„¸ íˆ¬ìž  ë¦¬í ¬íŠ¸": "상세 투자 리포트",
    "ì‹œê°€ ì´ ì•¡": "시가 총액",
    "ê±°ëž˜ëŸ‰ ë¹„ìœ¨": "거래량 비율",
    "ì¢…í•© ì  ìˆ˜": "종합 점수",
    "ì‹ í˜¸ ê°•ë „": "신호 강도",
    "ë§¤ìš° ê°•ë ¥": "매우 강력",
    "í•µì‹¬ ëª¨ë‹ˆí„°ë§  ë¦¬ìŠ¤í ¬": "핵심 모니터링 리스크",
    "ìž ìœ¨ì£¼í–‰ ë°  ì—£ì§€ AI ì‹œìž¥ í™•ëŒ€": "자율주행 및 엣지 AI 시장 확대",
    "ì¤‘êµ­ ìˆ˜ì¶œ ê·œì œ ë°  ê²½ìŸ  ì‹¬í™”": "중국 수출 규제 및 경쟁 심화",
    "ì  ì •ê°€ (DCF)": "적정가 (DCF)",
    "ìƒ ìŠ¹ ì—¬ë ¥": "상승 여력",
    "ê¸°ë³¸ ì§€í‘œ & ê¸°ìˆ ì   ë¶„ì„ ": "기본 지표 & 기술적 분석",
    "DCF ì  ì •ê°€ & ì‹œë‚˜ë¦¬ì˜¤": "DCF 적정가 & 시나리오",
    "SWOT & ë¦¬ìŠ¤í ¬ ë¶„ì„ ": "SWOT & 리스크 분석",
    "ESG & í”¼ì–´ ë¹„êµ  ë¶„ì„ ": "ESG & 피어 비교 분석",
    "ë°±í…ŒìŠ¤íŠ¸ ê²€ì¦  ì™„ë£Œ": "백테스트 검증 완료",
    "AI ë§¤ë§¤ ì‹ í˜¸ ìƒ ì„±": "AI 매매 신호 생성",
    "ì‹¤ì‹œê°„ ìŠ¤ë§ˆíŠ¸ ë¨¸ë‹ˆ": "실시간 스마트 머니",
    "ì—…ë °ì ´íŠ¸": "업데이트",
    "ë‹¤ìš´ë¡œë“œ": "다운로드",
    "ìˆœìœ„": "순위",
    "í‹°ì»¤": "티커",
    "ì„¹í„°": "섹터",
    "AI ì  ìˆ˜": "AI 점수",
    "ìƒ íƒœ": "상태",
    "í˜„ìž¬ê°€": "현재가",
    "ë“±ë ½": "등락",
    "ì‹œìž¥ í  ë¦„ (ì „ì²´)": "시장 흐름 (전체)",
    "ì‹¤ì‹œê°„": "실시간",
    "ì‹œìž¥ ì‹¬ë¦¬ ì§€ìˆ˜": "시장 심리 지수",
    "íƒ ìš•": "탐욕",
    "í˜„ìž¬ ì‹œìž¥ì €": "현재 시장은",
    "ë‹¨ê³„ë¥¼ ë³´ì ´ê³  ìžˆìŠµë‹ˆë‹¤": "단계를 보이고 있습니다",
    "ê¸°íšŒ ìš”ì ¸": "기회 요인",
    "ë¦¬ìŠ¤í ¬": "리스크",
    "ì£¼ìš” ê²½ì œ ì ¼ì •": "주요 경제 일정",
    "ETF ìž ê¸ˆ í  ë¦„": "ETF 자금 흐름",
    "ìœ ìž…": "유입",
    "ìœ ì¶œ": "유출",
    "ì „ë§ ": "전망",
    "ë¦¬ìŠ¤í ¬:": "리스크:",
    "ì ¼ +": "일 +",
    "ì£¼ +": "주 +",
    "ê°œì›” +": "개월 +"
}

path = r'c:\Users\mjang\Downloads\미국 종목 분석\templates\index.html'

try:
    with open(path, 'rb') as f:
        raw_data = f.read()
    
    # Try to decode what was written by PowerShell (likely interpreted as Latin1/Windows-1252)
    # The mojibake "ë¯¸êµ­" is characteristic of UTF-8 bytes being read as individual characters.
    # We will try to decode as UTF-8 (which will fail for corrupt parts) or just replace the known bad strings.
    
    # Since the file was saved with UTF-8 encoding in PS but the source was already read wrong,
    # the bytes are literally the hex codes for 'ë', '¯', etc.
    
    text = raw_data.decode('utf-8', errors='ignore')
    
    for bad, good in korean_replacements.items():
        text = text.replace(bad, good)
        
    # Also fix some UI logic that might have been broken by the same encoding mess
    text = text.replace('âœ…', '✅')
    text = text.replace('âš ï¸ ', '⚠️')
    text = text.replace('â °', '🕒')
    text = text.replace('ðŸš€', '🚀')
    text = text.replace('â†’', '→')
    text = text.replace('â†‘', '↑')
    text = text.replace('â†“', '↓')
    text = text.replace('ðŸ »', '🐻')
    text = text.replace('ðŸ“Š', '📊')
    text = text.replace('ðŸ ‚', '🐂')
    text = text.replace('ðŸ’°', '💰')
    text = text.replace('âœ¨', '✨')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS: Encoding restored using Python UTF-8 write.")

except Exception as e:
    print(f"FAILURE: {e}")
