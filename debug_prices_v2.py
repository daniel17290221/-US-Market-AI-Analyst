
import requests
import json

def fetch_realtime_data(tickers):
    prices = {}
    print(f"DEBUG: Fetching prices for {tickers}")
    
    for ticker in tickers:
        try:
            # Try v8/finance/chart which is often more stable
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"Status for {ticker}: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
                price = meta.get('regularMarketPrice')
                prev_close = meta.get('previousClose')
                
                if price and prev_close:
                    change = round(((price - prev_close) / prev_close) * 100, 2)
                    prices[ticker] = {'price': price, 'change': change}
                    print(f"SUCCESS: {ticker} = {price} ({change}%)")
                else:
                    print(f"MISSING: Data in JSON for {ticker}")
            else:
                print(f"FAILED: {ticker} status {resp.status_code}")
                
        except Exception as e:
            print(f"ERROR: {ticker} error: {e}")
    return prices

test_tickers = ['NVDA', 'TSLA', 'AAPL']
results = fetch_realtime_data(test_tickers)
print("\nFinal Results:")
print(json.dumps(results, indent=2))
