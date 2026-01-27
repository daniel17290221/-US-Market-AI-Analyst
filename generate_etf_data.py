
import os
import csv
from datetime import datetime

# Path where the API expects the file
base_dir = "."
data_dir = "us_market"
output_file = os.path.join(data_dir, "us_etf_flows.csv")

# Ensure directory exists
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Define fresh ETF flow data
# flow_score >= 70: Strong Inflow, < 45: Outflow
data = [
    {"ticker": "SPY", "name": "SPDR S&P 500", "category": "Broad Market", "current_price": 585.12, "flow_score": 85.5, "price_change_20d": 2.4},
    {"ticker": "QQQ", "name": "Invesco QQQ", "category": "Broad Market", "current_price": 515.30, "flow_score": 82.1, "price_change_20d": 3.1},
    {"ticker": "VOO", "name": "Vanguard S&P 500", "category": "Broad Market", "current_price": 535.40, "flow_score": 78.5, "price_change_20d": 2.2},
    {"ticker": "VTI", "name": "Vanguard Total", "category": "Broad Market", "current_price": 285.20, "flow_score": 75.2, "price_change_20d": 1.8},
    {"ticker": "XLK", "name": "Technology", "category": "Sector", "current_price": 225.10, "flow_score": 92.0, "price_change_20d": 5.4},
    {"ticker": "XLF", "name": "Financials", "category": "Sector", "current_price": 45.30, "flow_score": 72.4, "price_change_20d": 1.5},
    {"ticker": "GLD", "name": "Gold", "category": "Commodity", "current_price": 185.20, "flow_score": 65.0, "price_change_20d": 0.5},
    
    # Outflows (Scores < 45)
    {"ticker": "XLU", "name": "Utilities", "category": "Sector", "current_price": 72.10, "flow_score": 35.5, "price_change_20d": -2.4},
    {"ticker": "XLRE", "name": "Real Estate", "category": "Sector", "current_price": 38.50, "flow_score": 32.1, "price_change_20d": -3.1},
    {"ticker": "USO", "name": "Oil", "category": "Commodity", "current_price": 75.40, "flow_score": 40.5, "price_change_20d": -4.2},
    {"ticker": "TLT", "name": "20Y+ Treasury", "category": "Fixed Income", "current_price": 92.20, "flow_score": 25.4, "price_change_20d": -5.1},
    {"ticker": "EEM", "name": "Emerging Markets", "category": "International", "current_price": 42.10, "flow_score": 38.0, "price_change_20d": -1.2}
]

# Write to CSV
keys = data[0].keys()
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=keys)
    writer.writeheader()
    writer.writerows(data)

print(f"SUCCESS: ETF Flow data generated.")
