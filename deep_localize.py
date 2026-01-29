
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Further JavaScript string localization
    replacements = {
        'Analysis Ready.': '분석 완료.',
        'Market Sync Mode.': '시장 데이터 동기화 모드입니다.',
        'Normal.': '정상 범위입니다.',
        'No significant alerts.': '특이사항 없습니다.',
        'Fetching Events...': '일정 수집 중...',
        '시장 심리 지수는 현재': '현재 시장 심리는',
        '단계입니다.': ' 단계입니다.',
        'Outlook:': '전망:',
        'Risks:': '리스크:'
    }

    for eng, kor in replacements.items():
        content = content.replace(eng, kor)

    # UI label precision
    content = content.replace('MJANG CONNECT', '실시간 데이터 연결됨')
    content = content.replace('점수: 96 / 100', 'AI 점수: 96 / 100')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("SUCCESS: Deep localization of JS and UI labels.")

except Exception as e:
    print(f"ERROR: {e}")
