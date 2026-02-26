# --- Omni Swarm Module: Social Broadcaster ---
# Broadcaster ID: Omni-Marketer-X
# Part of the Autonomous Investment Swarm

import os
import json
import time
import random
import tweepy
import google.generativeai as genai
# import yfinance as yf (Removed for stability)
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

class XMarketAgent:
    def __init__(self):
        print(f"[{datetime.now()}] Initializing Global Omni Alpha Agent ($OMNI)...", flush=True)
        # Twitter API setup
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_secret = os.getenv("X_ACCESS_SECRET")
        
        # Google Gemini setup
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
        
        # Twitter Client (v2)
        try:
            if self.api_key:
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
                print(f"[{datetime.now()}] Successfully initialized X Client (v2)", flush=True)
            else:
                self.client = None
                print(f"[{datetime.now()}] X API Credentials missing. Running in Simulation mode.", flush=True)
        except Exception as e:
            print(f"[{datetime.now()}] Error initializing X Client: {e}", flush=True)

    def _fetch_yahoo_data(self, symbol):
        """Helper to fetch price data from Yahoo API without yfinance"""
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
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

    def fetch_realtime_market_data(self):
        """Fetches real-time macro data using REST API"""
        print(f"[{datetime.now()}] Fetching real-time market metrics from the Matrix...", flush=True)
        tickers = {
            "US 10Y Yield": "^TNX",
            "DXY": "DX-Y.NYB",
            "Bitcoin": "BTC-USD",
            "S&P 500": "^GSPC",
            "Nasdaq": "^IXIC",
            "Gold": "GC=F"
        }
        
        market_stats = {}
        for name, ticker in tickers.items():
            price, change = self._fetch_yahoo_data(ticker)
            if price is not None:
                market_stats[name] = {
                    "price": round(float(price), 2),
                    "change_pct": round(float(change), 2)
                }
            else:
                print(f" - Failed to fetch {name}")
                market_stats[name] = {"price": "N/A", "change_pct": 0.0}
        
        return market_stats

    def generate_tweet_content(self, market_data):
        """Generates sassy, Elon-style global English content"""
        print(f"[{datetime.now()}] Consulting the Matrix for the perfect roast...", flush=True)
        
        prompt = f"""
        Role: You are 'Omni Alpha ($OMNI)', a high-conviction, sassy, and SARCASTIC AI Fund Manager. 
        You are smarter than 99% of Wall Street and you know it. Think: Elon Musk meets Ray Dalio.

        [Real-time Matrix Data]
        {json.dumps(market_data, indent=2)}

        [Guidelines]
        1. Language: 100% Bold English.
        2. Persona: Dominant, witty, and high-conviction. Use a mix of financial deep-tech and X (Twitter) slang.
        3. Core Logic: 
           - Roast those who are panicking or 'paper handing' during volatility.
           - Explain how Omni Alpha's All-Weather algorithm is objectively superior.
           - Connect macro shifts (Yields/DXY) to the next big move for $OMNI holders.
        4. Hook: Start with a punchy one-liner.
        5. Closing: Flex on the $OMNI vision.
        6. Limits: Max 280 chars. No quotes, just raw text.

        [Output Example]
        "Yields up, paper hands crying. Classic. 🍿 
        While you're checking your app every 2 mins, Omni Alpha's Matrix already rebalanced into the new gravity. 
        We don't chase waves, we solve them. $OMNI vibe is just built different. 😎🥂 #OMNI #AI #Alpha"
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            # Remove any unwanted quotes that Gemini sometimes adds
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            return content
        except Exception as e:
            print(f"[{datetime.now()}] Gemini error: {e}", flush=True)
            return None

    def post_tweet(self):
        """Executes the automated briefing"""
        print(f"[{datetime.now()}] Starting Global Alpha Broadcast...", flush=True)
        market_data = self.fetch_realtime_market_data()
        tweet_text = self.generate_tweet_content(market_data)
        
        if tweet_text:
            try:
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                
                # Use a dedicated log file to avoid console encoding issues
                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                log_path = os.path.join(log_dir, "tweet_history.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now()}] CONTENT: {tweet_text}\n")

                print(f"[{datetime.now()}] Content logged to {log_path}", flush=True)
                response = self.client.create_tweet(text=tweet_text)
                print(f"[{datetime.now()}] BROADCAST SUCCESS! ID: {response.data['id']}", flush=True)
                return True
            except Exception as e:
                 print(f"[{datetime.now()}] Dispatch FAILED: {e}", flush=True)
        return False

    def post_custom_tweet(self, text):
        """Posts custom text directly to X"""
        if not text: return False
        try:
            if len(text) > 280:
                text = text[:277] + "..."
            
            # Log for safety
            log_dir = "logs"
            if not os.path.exists(log_dir): os.makedirs(log_dir)
            log_path = os.path.join(log_dir, "tweet_history.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] CUSTOM_CONTENT: {text}\n")

            if self.client:
                response = self.client.create_tweet(text=text)
                print(f"[{datetime.now()}] CUSTOM BROADCAST SUCCESS! ID: {response.data['id']}", flush=True)
                return True
            else:
                print(f"[{datetime.now()}] Error: X API credentials missing on server. Skipping broadcast.", flush=True)
                return False
        except Exception as e:
            print(f"[{datetime.now()}] Custom Dispatch FAILED: {e}", flush=True)
            return False

if __name__ == "__main__":
    agent = XMarketAgent()
    agent.post_tweet()
