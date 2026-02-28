import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8')

print("=== 1. Vercel API - 주도주 현재가/등락률 ===")
try:
    r = requests.get('https://us-market-ai-analyst.vercel.app/api/kr/market-data', timeout=15)
    print(f"Status: {r.status_code}")
    d = r.json()
    leaders = d.get('leaders_kospi', [])
    print(f"leaders_kospi: {len(leaders)}개")
    for s in leaders[:3]:
        print(f"  {s.get('name')} | 현재가: {s.get('price')} | 등락률: {s.get('change')}")
except Exception as e:
    print(f"Error: {e}")

print()
print("=== 2. GitHub Pages 리포트 확인 ===")
try:
    r2 = requests.get('https://daniel17290221.github.io/report_kr.html', timeout=10)
    print(f"Status: {r2.status_code}")
    title = re.search(r'<title>(.*?)</title>', r2.text)
    section_count = len(re.findall(r'article-section', r2.text))
    print(f"제목: {title.group(1) if title else 'N/A'}")
    print(f"분석 섹션 수: {section_count}")
    print(f"광고 코드 포함: {'adsbygoogle' in r2.text}")
    print(f"빈 내용(fallback): {'데이터 수집 중' in r2.text}")
    print(f"Content 크기: {len(r2.text)} bytes")
except Exception as e:
    print(f"Error: {e}")

print()
print("=== 3. Vercel KR 리포트 API ===")
try:
    r3 = requests.get('https://us-market-ai-analyst.vercel.app/api/kr/report', timeout=10)
    print(f"Status: {r3.status_code}")
    title3 = re.search(r'<title>(.*?)</title>', r3.text)
    print(f"제목: {title3.group(1) if title3 else 'N/A'}")
    print(f"광고 코드 포함: {'adsbygoogle' in r3.text}")
    print(f"빈 내용(fallback): {'데이터 수집 중' in r3.text}")
except Exception as e:
    print(f"Error: {e}")
