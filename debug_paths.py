import os
import sys
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'us_market')
filename = 'smart_money_picks_v2.csv'

print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIR: {DATA_DIR}")

possible_paths = [
    os.path.join(DATA_DIR, filename),
    os.path.join(os.getcwd(), 'us_market', filename),
    os.path.join(os.getcwd(), filename),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'us_market', filename))
]

for path in possible_paths:
    exists = os.path.exists(path)
    print(f"Path: {path} | Exexists: {exists}")
    if exists:
        print(f"  Size: {os.path.getsize(path)}")
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                print(f"  Rows loaded: {len(data)}")
                if data:
                    print(f"  First row: {data[0]}")
        except Exception as e:
            print(f"  Error loading: {e}")

report_path = os.path.join(DATA_DIR, 'us_market_morning_report.html')
print(f"Report Path: {report_path} | Exexists: {os.path.exists(report_path)}")
if os.path.exists(report_path):
    print(f"  Last Modified: {os.path.getmtime(report_path)}")
