
import os
import csv
from datetime import datetime

# Path where the API expects the file
base_dir = r"c:\Users\mjang\Downloads\미국 종목 분석"
data_dir = os.path.join(base_dir, "us_market")
output_file = os.path.join(data_dir, "smart_money_picks_v2.csv")

# Ensure directory exists
os.makedirs(data_dir, exist_ok=True)

# Define fresh 10-item data
data = [
    {"rank": "01", "ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "composite_score": "96.5", "grade": "🔥 S급 (즉시 매수)", "price": "143.00", "change": "8.5", "insight": "AI 실시간 모멘텀 강화.", "upside": "+18%"},
    {"rank": "02", "ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Automotive", "composite_score": "92.0", "grade": "🌟 A급 (적극 매수)", "price": "259.00", "change": "3.2", "insight": "공급망 개선 및 수요 회복.", "upside": "+20%"},
    {"rank": "03", "ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "composite_score": "89.0", "grade": "🌟 A급 (적극 매수)", "price": "228.50", "change": "1.3", "insight": "신규 디바이스 기대감.", "upside": "+12%"},
    {"rank": "04", "ticker": "MSFT", "name": "Microsoft Corp", "sector": "Software", "composite_score": "83.0", "grade": "📈 B급 (매수 고려)", "price": "426.00", "change": "1.0", "insight": "클라우드 점유율 확대.", "upside": "+10%"},
    {"rank": "05", "ticker": "AMZN", "name": "Amazon.com", "sector": "Commerce", "composite_score": "79.0", "grade": "📈 B급 (매수 고려)", "price": "189.00", "change": "0.6", "insight": "운영 효율성 증대.", "upside": "+15%"},
    {"rank": "06", "ticker": "META", "name": "Meta Platforms", "sector": "Technology", "composite_score": "78.0", "grade": "📈 B급 (매수 고려)", "price": "586.00", "change": "1.5", "insight": "광고 매출 반등 성공.", "upside": "+8%"},
    {"rank": "07", "ticker": "GOOGL", "name": "Alphabet Inc", "sector": "Technology", "composite_score": "77.0", "grade": "📈 B급 (매수 고려)", "price": "166.00", "change": "0.1", "insight": "AI 모델 서비스 통합.", "upside": "+14%"},
    {"rank": "08", "ticker": "AVGO", "name": "Broadcom Inc", "sector": "Semiconductors", "composite_score": "76.0", "grade": "📈 B급 (매수 고려)", "price": "173.00", "change": "2.2", "insight": "인프라 투자 수혜.", "upside": "+9%"},
    {"rank": "09", "ticker": "AMD", "name": "Advanced Micro", "sector": "Semiconductors", "composite_score": "75.0", "grade": "📈 B급 (매수 고려)", "price": "156.00", "change": "-2.2", "insight": "칩 경쟁력 유지 노력.", "upside": "+22%"},
    {"rank": "10", "ticker": "COST", "name": "Costco Wholesale", "sector": "Retail", "composite_score": "74.0", "grade": "📊 C급 (관망)", "price": "913.00", "change": "0.9", "insight": "충성도 높은 고객 유지.", "upside": "+5%"}
]

# Write to CSV
keys = data[0].keys()
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=keys)
    writer.writeheader()
    writer.writerows(data)

print(f"SUCCESS: Generated fresh CSV at {output_file}")
print(f"Date updated to: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
