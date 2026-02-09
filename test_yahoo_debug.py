import requests
import json

def fetch_test(ticker):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
    print(f"Fetching {url}...")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # Dump structure
            # print(json.dumps(data, indent=2))
            
            result = data.get('chart', {}).get('result')
            if result:
                meta = result[0].get('meta', {})
                price = meta.get('regularMarketPrice')
                prev_close = meta.get('chartPreviousClose', meta.get('previousClose'))
                
                print(f"Ticker: {ticker}")
                print(f"Price: {price}")
                print(f"Prev Close: {prev_close}")
                
                if price is not None and prev_close is not None:
                     change_pct = ((price - prev_close) / prev_close) * 100 if prev_close != 0 else 0.0
                     print(f"Calculated Change: {change_pct}")
                else:
                    print("Price or Prev Close is None")
            else:
                print("No 'result' in chart data")
        else:
            print("Response not 200")
            print(resp.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_test("005930.KS") # Samsung Electronics
    fetch_test("247540.KQ") # Ecopro BM
