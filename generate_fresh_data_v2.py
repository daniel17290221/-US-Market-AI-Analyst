
import os
import csv
from datetime import datetime

# Path where the API expects the file
# Use a safer string approach for Windows terminal
base_dir = "." # Current directory is fine as we are in the root
data_dir = "us_market"
output_file = os.path.join(data_dir, "smart_money_picks_v2.csv")

# Ensure directory exists
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Define fresh 10-item data
data = [
    {"rank": "01", "ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "composite_score": "96.5", "grade": "S grade", "price": "143.00", "change": "8.5", "insight": "AI momentum strengthening.", "upside": "+18%"},
    {"rank": "02", "ticker": "TSLA", "name": "Tesla, Inc.", "sector": "Automotive", "composite_score": "92.0", "grade": "A grade", "price": "259.00", "change": "3.2", "insight": "Supply chain improving.", "upside": "+20%"},
    {"rank": "03", "ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "composite_score": "89.0", "grade": "A grade", "price": "228.50", "change": "1.3", "insight": "Device demand high.", "upside": "+12%"},
    {"rank": "04", "ticker": "MSFT", "name": "Microsoft Corp", "sector": "Software", "composite_score": "83.0", "grade": "B grade", "price": "426.00", "change": "1.0", "insight": "Cloud market share up.", "upside": "+10%"},
    {"rank": "05", "ticker": "AMZN", "name": "Amazon.com", "sector": "Commerce", "composite_score": "79.0", "grade": "B grade", "price": "189.00", "change": "0.6", "insight": "Ops efficiency gains.", "upside": "+15%"},
    {"rank": "06", "ticker": "META", "name": "Meta Platforms", "sector": "Technology", "composite_score": "78.0", "grade": "B grade", "price": "586.00", "change": "1.5", "insight": "Ad revenue rebound.", "upside": "+8%"},
    {"rank": "07", "ticker": "GOOGL", "name": "Alphabet Inc", "sector": "Technology", "composite_score": "77.0", "grade": "B grade", "price": "166.00", "change": "0.1", "insight": "AI integrated services.", "upside": "+14%"},
    {"rank": "08", "ticker": "AVGO", "name": "Broadcom Inc", "sector": "Semiconductors", "composite_score": "76.0", "grade": "B grade", "price": "173.00", "change": "2.2", "insight": "Infra spend tailwinds.", "upside": "+9%"},
    {"rank": "09", "ticker": "AMD", "name": "Advanced Micro", "sector": "Semiconductors", "composite_score": "75.0", "grade": "B grade", "price": "156.00", "change": "-2.2", "insight": "Chip competitiveness.", "upside": "+22%"},
    {"rank": "10", "ticker": "COST", "name": "Costco Wholesale", "sector": "Retail", "composite_score": "74.0", "grade": "C grade", "price": "913.00", "change": "0.9", "insight": "High member loyalty.", "upside": "+5%"}
]

# Write to CSV
keys = data[0].keys()
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=keys)
    writer.writeheader()
    writer.writerows(data)

print(f"SUCCESS: Data generated.")
