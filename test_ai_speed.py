
import time
import os
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Setup same as api/index.py
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("No API Key found")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

print("Available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

# Using 2.0 Flash as in main code? Or 1.5? Main code uses 'gemini-2.0-flash-exp' usually if I set it, let's check index.py imports or just default.
# I'll Assume 2.0 Flash for speed
model = genai.GenerativeModel('gemini-1.5-flash')

stocks = [
    {'symbol': '005930', 'name': '삼성전자'},
    {'symbol': '000660', 'name': 'SK하이닉스'},
    {'symbol': '005380', 'name': '현대차'},
    {'symbol': '373220', 'name': 'LG에너지솔루션'},
    {'symbol': '005490', 'name': 'POSCO홀딩스'}
]

print("Starting AI request for 5 stocks...")
start = time.time()

prompt = f"""
Analyze these KR stocks. Return JSON with keys: insight, risk, swot_s, swot_w, swot_o, swot_t, dcf_target, dcf_bear, dcf_bull, upside.
Input: {json.dumps(stocks)}
JSON Only.
"""

try:
    response = model.generate_content(prompt)
    print(f"Response received. Length: {len(response.text)}")
except Exception as e:
    print(f"Error: {e}")

end = time.time()
print(f"Time taken: {end - start:.2f} seconds")
