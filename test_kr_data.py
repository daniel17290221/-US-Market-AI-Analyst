import yfinance as yf
symbol = "000660"
ticker_sym = f"{symbol}.KS"
ticker = yf.Ticker(ticker_sym)
df = ticker.history(period="6mo")
if df.empty:
    ticker_sym = f"{symbol}.KQ"
    ticker = yf.Ticker(ticker_sym)
    df = ticker.history(period="6mo")

print(f"Data found for {ticker_sym}: {len(df)} rows")
if not df.empty:
    print(df.tail(2))
