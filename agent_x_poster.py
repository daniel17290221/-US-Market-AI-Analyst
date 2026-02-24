import os
import json
import time
import random
import tweepy
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

class XMarketAgent:
    def __init__(self):
        print(f"[{datetime.now()}] Initializing XMarketAgent...", flush=True)
        # Twitter API setup
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_secret = os.getenv("X_ACCESS_SECRET")
        
        # Google Gemini setup
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Masked credential debug logging
        def mask(s):
            if not s: return "None"
            return s[:4] + "*" * (len(s)-8) + s[-4:] if len(s) > 8 else "****"

        print(f"[{datetime.now()}] Credential Check:", flush=True)
        print(f" - X_API_KEY: {mask(self.api_key)}", flush=True)
        print(f" - X_ACCESS_TOKEN: {mask(self.access_token)}", flush=True)
        print(f" - GEMINI_KEY: {mask(self.gemini_key)}", flush=True)

        # Twitter Client (v2)
        try:
            if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
                print(f"[{datetime.now()}] ERROR: Some Twitter API keys are MISSING in environment variables!", flush=True)
            
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )
            print(f"[{datetime.now()}] Successfully initialized X Client (v2)", flush=True)
        except Exception as e:
            print(f"[{datetime.now()}] Error initializing X Client: {e}", flush=True)

    def load_market_data(self):
        """Loads the latest analysis data from the local file system"""
        paths = [
            'us_market/us_ai_analysis.json',
            'KR_Market_Analyst/kr_market/kr_daily_data.json'
        ]
        combined_data = {}
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        combined_data.update(data)
                        print(f"[{datetime.now()}] Loaded data from {path}", flush=True)
                except Exception as e:
                    print(f"[{datetime.now()}] Error loading {path}: {e}", flush=True)
        return combined_data

    def generate_tweet_content(self, data):
        """Uses Gemini to create an engaging tweet based on market analysis"""
        if not data:
            print(f"[{datetime.now()}] No data to generate tweet. Using fallback.", flush=True)
            return "오늘 글로벌 시장의 흐름을 분석 중입니다. 잠시 후 인사이트를 공유합니다! #AI_Agent #미국주식"

        # Pick 2-3 random items
        items = list(data.items())
        sample = random.sample(items, min(len(items), 3))
        
        print(f"[{datetime.now()}] Generating tweet content with Gemini 2.0...", flush=True)
        
        prompt = f"""
        당신은 24시간 시장을 감시하는 AI 전략가 'Alpha Operator'입니다.
        아래 시장 데이터를 기반으로 X(트위터)용 한글 브리핑을 140자 이내로 작성하세요.

        [데이터]
        {json.dumps(sample, ensure_ascii=False)}

        [지시 사항]
        - 전문적이면서 강력한 어조
        - 언급된 종목 중 하나를 강조
        - Virtuals.io의 '올웨더 매트릭스' 비전 언급
        - 해시태그: $VIRTUAL #AI_Agent #미국주식 #AllWeather
        """
        
        try:
            response = self.model.generate_content(prompt)
            print(f"[{datetime.now()}] Gemini Content Generated.", flush=True)
            return response.text.strip()
        except Exception as e:
            print(f"[{datetime.now()}] Gemini error: {e}", flush=True)
            return None

    def post_tweet(self):
        """Main action: Fetch data -> Generate content -> Post to X"""
        print(f"[{datetime.now()}] Starting automated briefing workflow...", flush=True)
        
        data = self.load_market_data()
        tweet_text = self.generate_tweet_content(data)
        
        if tweet_text:
            try:
                tweet_text = tweet_text.replace('```', '').replace('json', '').strip()
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                
                print(f"[{datetime.now()}] Sending tweet to X API...", flush=True)
                # Ensure we are using API v2 via Client
                response = self.client.create_tweet(text=tweet_text)
                print(f"[{datetime.now()}] Tweet successfully posted! ID: {response.data['id']}", flush=True)
                return True
            except Exception as e:
                print(f"[{datetime.now()}] FAILED to post tweet. Details:", flush=True)
                print(f"Error Type: {type(e)}", flush=True)
                print(f"Error Content: {e}", flush=True)
                
                if "401" in str(e):
                    print("HINT: 401 Unauthorized usually means tokens are invalid OR you didn't regenerate them after changing app permissions to 'Read and Write'.", flush=True)
        return False

if __name__ == "__main__":
    agent = XMarketAgent()
    agent.post_tweet()
