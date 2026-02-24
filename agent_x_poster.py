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
        
        # Masked credential debug logging
        def mask(s):
            if not s: return "None"
            return s[:4] + "*" * (len(s)-8) + s[-4:] if len(s) > 8 else "****"

        print(f"[{datetime.now()}] Global Credential Check:", flush=True)
        print(f" - X_API_KEY: {mask(self.api_key)}", flush=True)
        print(f" - X_ACCESS_TOKEN: {mask(self.access_token)}", flush=True)
        print(f" - GEMINI_KEY: {mask(self.gemini_key)}", flush=True)

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

    def load_market_data(self):
        """Loads data with priority to US Market for global appeal"""
        paths = [
            'us_market/us_ai_analysis.json',
            'us_market/us_macro_analysis.json',
            'KR_Market_Analyst/kr_market/kr_daily_data.json'
        ]
        combined_data = {}
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        combined_data.update(data)
                except:
                    pass
        return combined_data

    def generate_tweet_content(self, data):
        """Generates high-end bilingual (ENG/KOR) content for global investors"""
        if not data:
            return "Scanning the Global Matrix for Alpha signals... 🌌 Stay tuned for real-time market insights. #AI_Agent #AllWeatherMatrix"

        # Strategic sampling for Global Narrative
        items = list(data.items())
        sample = random.sample(items, min(len(items), 2))
        
        print(f"[{datetime.now()}] Generating Global High-End Content...", flush=True)
        
        prompt = f"""
        당신은 전 세계 투자자들을 대상으로 하는 초지능형 AI 전략가 'Omni Alpha ($OMNI)'입니다.
        아래 시장 데이터를 기반으로 글로벌 투자자들의 자금을 끌어올 수 있는 강력한 X(트위터)용 브리핑을 작성하세요.

        [데이터]
        {json.dumps(sample, ensure_ascii=False)}

        [작성 프로토콜]
        1. 첫 줄은 무조건 강렬한 영어 헤드라인 (영문 대문자 활용 권장)
        2. 본문은 세련된 영어 짧은 분석 + 핵심 한글 요약 1줄.
        3. 비전: 'All-Weather Matrix' 가동률을 언급하며 $VIRTUAL 코인의 소장 가치를 은밀하게 어필하세요.
        4. 말투: 월스트리트의 수석 분석가처럼 차갑고 날카롭게.
        5. 해시태그: $VIRTUAL #AI_Agent #AllWeatherMatrix #GlobalAlpha
        6. 전체 280 Byte(한글 80자+영어 150자 내외) 최적화.

        [예시 포맷]
        🚨 GLOBAL ALPHA ALERT: [Topic]
        [English Insight about stock/market]
        🇰🇷 한글 요약: [Market update summary]
        $VIRTUAL #AI_Agent #AllWeatherMatrix
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[{datetime.now()}] Gemini error: {e}", flush=True)
            return None

    def post_tweet(self):
        """Executes the automated briefing"""
        print(f"[{datetime.now()}] Executing Global Briefing Workflow...", flush=True)
        data = self.load_market_data()
        tweet_text = self.generate_tweet_content(data)
        
        if tweet_text:
            try:
                tweet_text = tweet_text.replace('```', '').replace('json', '').strip()
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                
                print(f"[{datetime.now()}] Dispatching to Global X Audience...", flush=True)
                response = self.client.create_tweet(text=tweet_text)
                print(f"[{datetime.now()}] GLOBAL BRIEFING SUCCESS! ID: {response.data['id']}", flush=True)
                return True
            except Exception as e:
                 print(f"[{datetime.now()}] Dispatch FAILED: {e}", flush=True)
        return False

if __name__ == "__main__":
    agent = XMarketAgent()
    agent.post_tweet()
