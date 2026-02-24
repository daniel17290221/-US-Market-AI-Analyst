
import os
import csv
import json

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'us_market')

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    data = []
    print(f"Checking path: {path}")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                print(f"Loaded {len(data)} items from file.")
        except Exception as e:
            print(f"Error loading CSV {filename}: {e}")
    
    if not data and filename == 'smart_money_picks_v2.csv':
        print("Using default fallback data.")
        return [
            {"rank": "01", "ticker": "NVDA", "name": "NVIDIA Corporation", "composite_score": "95.8"},
            {"rank": "02", "ticker": "TSLA", "name": "Tesla, Inc.", "composite_score": "91.2"}
        ]
    return data

data = load_csv('smart_money_picks_v2.csv')
print(f"Final Count: {len(data)}")
if data:
    print(f"First item: {data[0]}")
