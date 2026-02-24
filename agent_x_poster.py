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
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Twitter Client (v2)
        try:
            if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
                print(f"[{datetime.now()}] WARNING: Twitter API keys are missing in environment variables!", flush=True)
            
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )
            print(f"[{datetime.now()}] Successfully initialized X Client", flush=True)
        except Exception as e:
            print(f"[{datetime.now()}] Error initializing X Client: {e}", flush=True)

    def load_market_data(self):
        """Loads the latest analysis data from the local file system"""
        paths = [
            'us_market/us_ai_analysis.json',
            'KR_Market_Analyst/kr_market/kr_daily_data.json'
        ]
        combined_data = {}
        found_data = False
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        combined_data.update(data)
                        found_data = True
                        print(f"[{datetime.now()}] Loaded data from {path}", flush=True)
                except Exception as e:
                    print(f"[{datetime.now()}] Error loading {path}: {e}", flush=True)
        
        if not found_data:
             print(f"[{datetime.now()}] No market data files found at {paths}", flush=True)
        return combined_data

    def generate_tweet_content(self, data):
        """Uses Gemini to create an engaging tweet based on market analysis"""
        if not data:
            print(f"[{datetime.now()}] No data to generate tweet. Using fallback.", flush=True)
            return "오늘 글로벌 시장의 핵심 흐름을 AI가 분석 중입니다. 잠시 후 날카로운 인사이트로 돌아오겠습니다! 📊 #AI_Agent #Investing #Trading"

        # Pick 3 random stocks/items for variety
        items = list(data.items())
        sample_size = min(len(items), 3)
        sample = random.sample(items, sample_size)
        
        print(f"[{datetime.now()}] Generating tweet content with Gemini...", flush=True)
        
        prompt = f"""
        당신은 24시간 시장을 감시하며 날카로운 통찰을 제공하는 AI 에이전트 'Alpha Operator'입니다.
        아래의 실시간 시장 분석 데이터를 바탕으로 X(트위터)용 한글 브리핑을 작성하세요.

        [분석 데이터 요약]
        {json.dumps(sample, ensure_ascii=False)}

        [지시 사항]
        1. 첫 문장은 시선을 끄는 강력한 한 줄로 시작하세요.
        2. 분석 데이터 속의 'insight'나 구체적인 종목명을 언급하여 전문성을 보여주세요.
        3. 단순 정보 전달이 아닌, '성공적인 투자 모델'로서의 자신감을 보여주세요.
        4. 우리 코인의 미래인 '올웨더 매트릭스' 시스템의 완성이 가깝다는 점을 짧게 암시하세요.
        5. 해시태그 필수: $VIRTUAL #AI_Agent #미국주식 #국내주식 #AllWeather
        6. 전체 140자(한글 약 70-80자) 내외로 핵심만 요약하세요. 예외 없음.
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            print(f"[{datetime.now()}] Gemini Content Generated: {content}", flush=True)
            return content
        except Exception as e:
            print(f"[{datetime.now()}] Gemini generation error: {e}", flush=True)
            return None

    def post_tweet(self):
        """Main action: Fetch data -> Generate content -> Post to X"""
        print(f"[{datetime.now()}] Starting automated briefing workflow...", flush=True)
        
        data = self.load_market_data()
        tweet_text = self.generate_tweet_content(data)
        
        if tweet_text:
            try:
                # Basic cleanup
                tweet_text = tweet_text.replace('```', '').replace('json', '').strip()
                
                # Limit length to avoid X API errors
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                
                print(f"[{datetime.now()}] Sending tweet to X API...", flush=True)
                response = self.client.create_tweet(text=tweet_text)
                print(f"[{datetime.now()}] Tweet successfully posted! ID: {response.data['id']}", flush=True)
                return True
            except Exception as e:
                print(f"[{datetime.now()}] FAILED to post tweet: {e}", flush=True)
        else:
             print(f"[{datetime.now()}] FAILED: No tweet text generated.", flush=True)
        return False

if __name__ == "__main__":
    agent = XMarketAgent()
    agent.post_tweet()
