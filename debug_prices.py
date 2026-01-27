
import requests
import json

def fetch_realtime_data(tickers):
    prices = {}
    print(f"DEBUG: Fetching prices for {tickers}")
    
    for ticker in tickers:
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
            # Use more 'human' headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"Status for {ticker}: {resp.status_code}")
            data = resp.json()
            
            if 'quoteResponse' in data and data['quoteResponse']['result']:
                quote = data['quoteResponse']['result'][0]
                price = quote.get('regularMarketPrice')
                change = quote.get('regularMarketChangePercent')
                prices[ticker] = {'price': price, 'change': change}
                print(f"SUCCESS: {ticker} = {price}")
            else:
                print(f"EMPTY: Result set for {ticker} is empty.")
        except Exception as e:
            print(f"FAILED: {ticker} error: {e}")
    return prices

test_tickers = ['NVDA', 'TSLA', 'AAPL']
results = fetch_realtime_data(test_tickers)
print("\nFinal Results:")
print(json.dumps(results, indent=2))
