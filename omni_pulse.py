import os
import json
import pandas as pd
import requests
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import tweepy

# Load environment variables
load_dotenv()

class OmniPulse:
    def __init__(self):
        print(f"[{datetime.now()}] Initializing Omni Pulse (Real-time Emission)...", flush=True)
        # API Keys
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

        # Twitter Client
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_secret = os.getenv("X_ACCESS_SECRET")
        
        try:
            if self.api_key and self.access_token:
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
            else:
                self.client = None
        except Exception as e:
            print(f"X Init Error: {e}")
            self.client = None

    def fetch_market_pulse(self):
        """Fetches super quick real-time prices for major assets"""
        tickers = {
            "S&P500": "^GSPC",
            "Nasdaq": "^IXIC",
            "Bitcoin": "BTC-USD",
            "DXY": "DX-Y.NYB",
            "NVDA": "NVDA",
            "TSLA": "TSLA"
        }
        pulse_data = {}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for name, ticker in tickers.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1m&range=1d"
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    meta = resp.json()['chart']['result'][0]['meta']
                    pulse_data[name] = {
                        "price": meta.get('regularMarketPrice'),
                        "change": round(((meta.get('regularMarketPrice') - meta.get('previousClose')) / meta.get('previousClose')) * 100, 2)
                    }
            except:
                pulse_data[name] = {"price": "N/A", "change": 0.0}
        return pulse_data

    def generate_pulse_tweet(self, data):
        if not self.model: return None
        
        prompt = f"""
        Role: You are 'Omni Alpha' ($OMNI), a high-conviction AI Fund Manager on the Virtuals Protocol.
        Market Snapshot: {json.dumps(data)}
        
        Task: Write a SHARP, SHORT real-time market pulse tweet. 
        - Roast any panic or irrational exuberance.
        - provide one high-signal insight based on these prices.
        - Mention that your AI Swarm is analyzing deep flows in real-time.
        - Language: English. Bold/Witty.
        - Max 250 chars. Include $OMNI #VirtualsProtocol #MarketPulse.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('"', '')
        except:
            return None

    def execute(self):
        data = self.fetch_market_pulse()
        tweet = self.generate_pulse_tweet(data)
        
        if tweet:
            print(f"Pulse: {tweet}")
            if self.client:
                try:
                    self.client.create_tweet(text=tweet)
                    print("Pulse broadcasted successfully.")
                except Exception as e:
                    print(f"Broadcast failed: {e}")
            else:
                print("Simulation mode.")

if __name__ == "__main__":
    Pulse = OmniPulse()
    Pulse.execute()
