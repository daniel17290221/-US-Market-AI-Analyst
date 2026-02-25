import os
import json
import time
import random
import tweepy
import google.generativeai as genai
# import yfinance as yf # Removed for Vercel
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Twitter Client (v2)
        try:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )
            print(f"[{datetime.now()}] Successfully initialized X Client (v2)", flush=True)
        except Exception as e:
            print(f"[{datetime.now()}] Error initializing X Client: {e}", flush=True)

    def fetch_realtime_market_data(self):
        """Fetches real-time macro data using yfinance"""
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
            try:
                data = yf.Ticker(ticker)
                hist = data.history(period="5d") # Increased period to ensure data
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = ((current_price - prev_price) / prev_price) * 100
                    market_stats[name] = {
                        "price": round(float(current_price), 2),
                        "change_pct": round(float(change), 2)
                    }
                else:
                    print(f" - Insufficient data for {name}")
            except Exception as e:
                print(f" - Failed to fetch {name}: {e}")
        
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
                # response = self.client.create_tweet(text=tweet_text) # Commented out until API limit reset
                # print(f"[{datetime.now()}] BROADCAST SUCCESS! ID: {response.data['id']}", flush=True)
                print(f"[{datetime.now()}] [DRY RUN] Would have posted: {tweet_text}", flush=True)
                return True
            except Exception as e:
                 print(f"[{datetime.now()}] Dispatch FAILED: {e}", flush=True)
        return False

if __name__ == "__main__":
    agent = XMarketAgent()
    agent.post_tweet()
