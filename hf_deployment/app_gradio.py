import os
import time
import json
import requests
import tweepy
import google.generativeai as genai
import gradio as gr
import threading
from datetime import datetime
from dotenv import load_dotenv

# Load env for local testing
load_dotenv()

class GradioXAgent:
    def __init__(self):
        print(f"[{datetime.now()}] Initializing OMNI Cloud Agent (Gradio version)...", flush=True)
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_secret = os.getenv("X_ACCESS_SECRET")
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

        try:
            if self.api_key and self.access_token:
                # Explicitly use OAuth 1.0a for Free Tier stability
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
                # Verify if we can post (Simple test happens later in post_update)
            else:
                self.client = None
        except Exception as e:
            print(f"Auth Error: {e}", flush=True)

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
                    p, pc = meta.get('regularMarketPrice'), meta.get('chartPreviousClose')
                    if p and pc: return p, ((p - pc) / pc) * 100
            return None, None
        except: return None, None

    def post_update(self):
        tickers = {"Bitcoin": "BTC-USD", "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Gold": "GC=F", "US 10Y Yield": "^TNX"}
        stats = {}
        for name, ticker in tickers.items():
            p, c = self._fetch_yahoo_data(ticker)
            if p: stats[name] = {"price": round(p, 2), "change": round(c, 2)}
        
        if not self.model or not self.client: return "Missing Auth/Model"

        prompt = f"Role: Sassy AI Fund Manager Omni Alpha ($OMNI). Context: {json.dumps(stats)}. Guideline: English, witty, roast paper hands. Closing: $OMNI vibe. Max 280 chars. No quotes."
        try:
            content = self.model.generate_content(prompt).text.strip().replace('"', '')
            if len(content) > 280: content = content[:277] + "..."
            self.client.create_tweet(text=content)
            return f"Success! Posted: {content}"
        except Exception as e:
            return f"Failed: {e}"

agent = GradioXAgent()

def run_loop():
    while True:
        print(f"[{datetime.now()}] Automatic post attempt...", flush=True)
        result = agent.post_update()
        print(result, flush=True)
        time.sleep(14400) # 4 hours

# Start background thread
threading.Thread(target=run_loop, daemon=True).start()

# Gradio UI
with gr.Blocks(title="Omni Alpha ($OMNI) - AI Agent") as demo:
    gr.Markdown("# 🛡️ Omni Alpha ($OMNI) Cloud Terminal")
    gr.Markdown("Status: **Active** | 24/7 Monitoring Enabled")
    
    with gr.Row():
        status_box = gr.Textbox(label="Last Activity", value="Waiting for first broadcast...")
    
    manual_btn = gr.Button("Manual Broadcast (Test)")
    manual_btn.click(fn=lambda: agent.post_update(), outputs=status_box)

demo.launch()
