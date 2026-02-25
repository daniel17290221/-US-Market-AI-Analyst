import os
import time
import json
import requests
import tweepy
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load env for local testing, but Hugging Face will use Secrets
load_dotenv()

class HuggingFaceXAgent:
    def __init__(self):
        print(f"[{datetime.now()}] Initializing $OMNI Cloud Agent on Hugging Face...", flush=True)
        # Auth stats
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_secret = os.getenv("X_ACCESS_SECRET")
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        
        # Google Gemini setup
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

        # Twitter Client
        try:
            if self.api_key and self.access_token:
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
                print(f"[{datetime.now()}] X Client (v2) Ready!", flush=True)
            else:
                self.client = None
                print("Missing X API Keys in Secrets!", flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)

    def _fetch_yahoo_data(self, symbol):
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                result = data.get('chart', {}).get('result')
                if result:
                    meta = result[0].get('meta', {})
                    price = meta.get('regularMarketPrice')
                    prev_close = meta.get('chartPreviousClose', meta.get('previousClose'))
                    if price is not None and prev_close is not None:
                        change_pct = ((price - prev_close) / prev_close) * 100 if prev_close != 0 else 0.0
                        return price, change_pct
            return None, None
        except Exception:
            return None, None

    def post_update(self):
        print(f"[{datetime.now()}] Executing Market Broadcast...", flush=True)
        tickers = {"Bitcoin": "BTC-USD", "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Gold": "GC=F", "US 10Y Yield": "^TNX"}
        stats = {}
        for name, ticker in tickers.items():
            p, c = self._fetch_yahoo_data(ticker)
            if p: stats[name] = {"price": round(p, 2), "change": round(c, 2)}
        
        if not self.model or not self.client:
            print("Missing AI or Twitter auth. Skipping.", flush=True)
            return

        prompt = f"Role: Sassy AI Fund Manager Omni Alpha ($OMNI). Context: {json.dumps(stats)}. Guideline: English, witty, roast paper hands. Closing: $OMNI vibe. Max 280 chars. No quotes."
        try:
            content = self.model.generate_content(prompt).text.strip().replace('"', '')
            if len(content) > 280: content = content[:277] + "..."
            
            resp = self.client.create_tweet(text=content)
            print(f"[{datetime.now()}] SUCCESS! Tweet ID: {resp.data['id']}", flush=True)
            print(f"Posted: {content}", flush=True)
        except Exception as e:
            print(f"Failed to post: {e}", flush=True)

if __name__ == "__main__":
    import streamlit as st
    st.title("Omni Alpha ($OMNI) Cloud Agent")
    st.write("Status: Active & Monitoring the Matrix...")
    
    agent = HuggingFaceXAgent()
    
    # Run loop
    while True:
        try:
            agent.post_update()
        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
        
        # Wait for 4 hours
        time.sleep(14400)
