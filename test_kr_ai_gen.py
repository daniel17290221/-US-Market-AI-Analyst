import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'KR_Market_Analyst'))
from kr_market.kr_report_generator import KRDailyReportGenerator
import json

# Load the test data we just created (if it's done)
try:
    with open('test_kr_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
except:
    print("Test data not found yet. Please wait for the other script.")
    sys.exit(1)

generator = KRDailyReportGenerator(data_dir=os.getcwd())
print("Starting AI generation test...")
ai_content = generator.generate_ai_content(raw_data)
print("AI Content generated:")
print(json.dumps(ai_content, indent=4, ensure_ascii=False))

# Check if it hit the fallback
if ai_content.get('catchy_title') == "코스피, 방향성 탐색 구간 진입":
    print("\nWARNING: Hit fallback content!")
else:
    print("\nSUCCESS: AI generated unique content.")
