import yfinance as yf
from datetime import datetime

def test():
    symbols = ['^GSPC', '^IXIC', '^DJI', 'CL=F', 'GC=F', 'BTC-USD']
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="2d")
            print(f"Symbol: {sym}")
            if not hist.empty:
                print(f"  Rows: {len(hist)}")
                print(f"  Last Close: {hist['Close'].iloc[-1]}")
            else:
                print("  EMPTY")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    test()
