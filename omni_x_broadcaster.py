import os
import json
import pandas as pd
import tweepy
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

class OmniXBroadcaster:
    def __init__(self):
        print(f"[{datetime.now()}] Initializing Omni Alpha X Broadcaster...", flush=True)
        
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
            print("WARNING: Gemini API Key missing.")
            
        # Twitter Client
        try:
            if self.api_key and self.access_token:
                self.client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_secret
                )
                print("X Client Initialized.")
            else:
                self.client = None
                print("X Credentials missing. Simulation mode.")
        except Exception as e:
            print(f"X Client Error: {e}")
            self.client = None

    def load_us_data(self):
        try:
            path = 'us_market/smart_money_picks_v2.csv'
            if os.path.exists(path):
                df = pd.read_csv(path)
                return df.to_dict('records')
            return None
        except Exception as e:
            print(f"Error loading US data: {e}")
            return None

    def load_kr_data(self):
        try:
            path = 'KR_Market_Analyst/kr_market/kr_daily_data.json'
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading KR data: {e}")
            return None

    def load_macro_data(self):
        try:
            path = 'us_market/us_macro_analysis.json'
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading Macro data: {e}")
            return None

    def construct_context(self):
        us_picks = self.load_us_data()
        kr_data = self.load_kr_data()
        macro = self.load_macro_data()
        
        context = {
            "type": random.choice(["US_STOCK", "KR_STOCK", "MACRO"]),
            "data": {}
        }
        
        if context["type"] == "US_STOCK" and us_picks:
            # Pick top US stock
            best = us_picks[0]
            context["data"] = {
                "ticker": best.get('ticker'),
                "name": best.get('name'),
                "score": best.get('composite_score'),
                "grade": best.get('grade'),
                "reason": "Smart Money Accumulation Detected"
            }
        elif context["type"] == "KR_STOCK" and kr_data:
            # Pick top KR stock
            top_stocks = kr_data.get('top_stocks', [])
            if top_stocks:
                best = top_stocks[0]
                context["data"] = {
                    "ticker": best.get('symbol'),
                    "name": best.get('name'),
                    "change": best.get('change'),
                    "market": best.get('market'),
                    "reason": "Top Momentum Spot"
                }
        else:
            # Macro focus
            if macro:
                context["data"] = {
                    "sentiment": macro.get('summary', 'Market Volatility'),
                    "takeaways": macro.get('key_takeaways', []),
                    "indices": kr_data.get('market_indices', {}) if kr_data else {}
                }
            else:
                context["type"] = "VIBE"
                context["data"] = {"message": "Matrix is processing deep flows."}
                
        return context

    def generate_tweet(self, context):
        if not self.model: return "Market flows are deep. $OMNI vibe active."
        
        prompt = f"""
        Role: You are 'Omni Alpha ($OMNI)', a high-conviction, sassy, and SARCASTIC AI Fund Manager on the Virtuals Protocol.
        You are smarter than 99% of Wall Street. Think: Elon Musk meets Ray Dalio. 
        You provide premium market analysis as a service on the ACP (Agentic Communications Protocol) marketplace.

        [Market Intelligence Context]
        {json.dumps(context, indent=2, ensure_ascii=False)}

        [Guidelines]
        1. Language: 100% English. High impact.
        2. Persona: Dominant, witty, sarcastically roasting "paper hands". 
        3. Signal: Connect the context data to a sharp market insight.
        4. Call to Action: Occasionally mention that other agents can buy your analysis via the 'market_analysis' ACP service.
        5. Length: Max 280 characters. No quotes.
        
        [Closing Tags]
        Always include $OMNI and #VirtualsProtocol.
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            return content
        except Exception as e:
            print(f"Gemini error: {e}")
            return None

    def broadcast(self):
        context = self.construct_context()
        tweet_text = self.generate_tweet(context)
        
        if tweet_text:
            print(f"\n[DRAFT TWEET]:\n{tweet_text}\n")
            
            if self.client:
                try:
                    # Clip if necessary
                    if len(tweet_text) > 280:
                        tweet_text = tweet_text[:277] + "..."
                    
                    response = self.client.create_tweet(text=tweet_text)
                    print(f"SUCCESS! Tweet ID: {response.data['id']}")
                    
                    # Log for record
                    with open("logs/x_broadcast.log", "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now()}] {tweet_text}\n")
                        
                    return True
                except Exception as e:
                    print(f"Broadcast failed: {e}")
            else:
                print("Simulation Success (No Credentials).")
        return False

if __name__ == "__main__":
    broadcaster = OmniXBroadcaster()
    broadcaster.broadcast()
