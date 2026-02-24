
import os
import csv
import sys

# Mocking the api/index.py environment
BASE_DIR = r"C:\Users\mjang\Downloads\Investment Vibecodinglab"
DATA_DIR = os.path.join(BASE_DIR, 'us_market')

def load_csv_verbose(filename):
    possible_paths = [
        os.path.join(DATA_DIR, filename),
        os.path.join(os.getcwd(), 'us_market', filename),
        os.path.join(os.getcwd(), filename),
        os.path.abspath(os.path.join(BASE_DIR, 'us_market', filename))
    ]
    
    print(f"\n--- Testing load_csv for {filename} ---")
    data = []
    path_to_use = None
    
    for path in possible_paths:
        print(f"DEBUG: Checking path: {path}")
        if os.path.exists(path):
            path_to_use = path
            print(f"DEBUG: FOUND file at {path}, size={os.path.getsize(path)}")
            break
            
    if not path_to_use:
        print("DEBUG: File NOT FOUND in any path.")
        return []

    for enc in ['utf-8-sig', 'utf-8', 'cp949']:
        print(f"DEBUG: Trying encoding: {enc}")
        try:
            with open(path_to_use, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames
                print(f"DEBUG: Header detected: {header}")
                
                if not header:
                    print(f"DEBUG: Header is NONE or EMPTY for {enc}")
                    continue
                
                temp_data = []
                for i, row in enumerate(reader):
                    if i == 0:
                        print(f"DEBUG: First row keys: {list(row.keys())}")
                    # print(f"DEBUG: First row values: {row.values()}")
                    temp_data.append(row)
                
                if temp_data:
                    print(f"DEBUG: Successfully read {len(temp_data)} rows with {enc}")
                    return temp_data
                else:
                    print(f"DEBUG: Read 0 rows with {enc} (EOF or empty file?)")
        except Exception as e:
            print(f"DEBUG: Error with {enc}: {e}")
            
    return []

if __name__ == "__main__":
    res = load_csv_verbose('smart_money_picks_v2.csv')
    print(f"\nFINAL RESULT: {len(res)} rows loaded.")
    if res:
        print(f"Top row ticker: {res[0].get('ticker', 'MISSING TICKER')}")
