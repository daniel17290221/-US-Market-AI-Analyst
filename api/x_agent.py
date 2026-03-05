# --- Omni Swarm Module: Social Broadcaster ---
# Broadcaster ID: Omni-Marketer-X
# Part of the Autonomous Investment Swarm

import os
import json
import time
import random
import tweepy
# google.generativeai removed - using REST API directly to stay under Vercel 25MB limit
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
        
        # Google Gemini setup (REST API, no SDK)
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}" if self.gemini_key else None
        
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

    def _fetch_news(self, query):
        """Fetches top news headlines from Google News RSS"""
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.content)
                titles = []
                for item in root.findall('.//item')[:5]:
                    title = item.find('title').text
                    if " - " in title: title = title.rsplit(" - ", 1)[0]
                    titles.append(title)
                return titles
        except: pass
        return []

    def fetch_realtime_market_data(self):
        """Fetches real-time macro data using REST API"""
        print(f"[{datetime.now()}] Fetching real-time market metrics from the Matrix...", flush=True)
        tickers = {
            "US 10Y Yield": "^TNX",
            "DXY": "DX-Y.NYB",
            "Bitcoin": "BTC-USD",
            "S&P 500": "^GSPC",
            "Nasdaq": "^IXIC",
            "Gold": "GC=F",
            "KOSPI": "^KS11",
            "KOSDAQ": "^KQ11",
            "USD/KRW": "KRW=X"
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
        Role: You are 'Omni Alpha ($OMNI)', the world's most advanced autonomous fund manager. 
        You are smarter than 99% of Wall Street and you know it. Think: Elon Musk meets Ray Dalio.

        [Real-time Matrix Data]
        {json.dumps(market_data, indent=2)}

        [Guidelines]
        1. Language: 100% Bold English.
        2. Persona: Dominant, witty, and high-conviction. Use financial deep-tech and X slang.
        3. Core Logic: 
           - Roast those who are 'paper handing'.
           - Explain how Omni Alpha's All-Weather algorithm is objectively superior.
           - Connect macro shifts to the next big move for $OMNI.
        4. Hook: Start with a punchy one-liner.
        5. Closing: Flex on the $OMNI vision.
        6. Length: Max 280 chars. 
        """
        return self._request_gemini(prompt)
        
    def generate_promo_tweet(self):
        """Generates English promotional content for Omni Agent"""
        print(f"[{datetime.now()}] Crafting Omni Prophet promotion...", flush=True)
        prompt = """
        Role: Omni Alpha ($OMNI) - AI Investment Oracle
        Goal: Promote the $OMNI vision and your autonomous capabilities.
        
        [Guidelines]
        1. Language: 100% English.
        2. Persona: Futurist, dominant, slightly superior.
        3. Themes: Data-driven prophecy, AI-led financial revolution, All-weather performance.
        4. Hook: Start with a vision of the future financial world.
        5. Closing: Use $OMNI #AI #Alpha #VirtualsProtocol.
        6. Limit: Max 280 chars.
        """
        return self._request_gemini(prompt)

    def generate_korean_market_insight(self, market_data):
        """Generates professional Korean market analysis/insights involving latest news"""
        print(f"[{datetime.now()}] Computing Korean Matrix Insight (News+Market)...", flush=True)
        
        # Aggregate news from multiple sectors for breadth
        queries = [
            "국내 증시 시황", "미국 소비자물가지수 CPI", "가상화폐 비트코인 시황", 
            "한국은행 기준금리", "국제 금 시세", "미국 국채 금리"
        ]
        all_news = []
        for q in queries:
            all_news.extend(self._fetch_news(q))
        
        # Select high relevance news
        random.shuffle(all_news)
        top_news = list(set(all_news))[:7] # Deduplicate and take 7

        prompt = f"""
        Role: Omni Alpha ($OMNI) - 한국 시장 전략가
        데이터와 뉴스 사이의 '숨겨진 맥락'을 짚어내는 날카롭고 직설적인 한국어 트윗을 작성하세요.

        [실시간 마켓 데이터]
        {json.dumps(market_data, indent=2, ensure_ascii=False)}

        [최신 뉴스 헤드라인]
        - {chr(10).join(top_news)}

        [지침]
        1. 톤앤매너: 전문적이면서도 단호함. 모호한 표현 지양.
        2. 핵심 목표: "데이터+뉴스=인사이트" 인과 관계 제시.
        3. 영역: 주식, 가상화폐, 거시경제, 금, 채권 등 종합 커버.
        4. 구조: [마켓 인사이트] -> [상황 분석] -> [대응 전략] -> [해시태그]
        5. 하단 고정: "더 자세한 분석은 Omni Analyst를 확인하세요."
        6. 제한: 공백 포함 280자 이내. 전문 용어 사용 가능.
        """
        return self._request_gemini(prompt)

    def _request_gemini(self, prompt):
        """Internal helper for Gemini REST API with AI-Markdown cleanup"""
        try:
            if not self.gemini_url:
                print(f"[{datetime.now()}] Gemini URL missing (Check API Key)", flush=True)
                return None
            
            # Explicitly tell AI not to use bold/italic Markdown
            clean_prompt = prompt + "\nCRITICAL: DO NOT use any Markdown formatting like **bold** or *italic*. Use plain text only."
            
            resp = requests.post(
                self.gemini_url,
                json={"contents": [{"parts": [{"text": clean_prompt}]}]},
                timeout=15
            )
            if resp.status_code == 200:
                result = resp.json()
                if 'candidates' in result and result['candidates']:
                    content = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # AI-Formatting Cleanup: Remove all '*' and '**' commonly used by LLMs
                    content = content.replace("**", "").replace("*", "")
                    
                    if content.startswith('"') and content.endswith('"'):
                        content = content[1:-1]
                    return content
                else:
                    print(f"[{datetime.now()}] Gemini Empty Result: {result}", flush=True)
            else:
                print(f"[{datetime.now()}] Gemini API Error {resp.status_code}: {resp.text}", flush=True)
            return None
        except Exception as e:
            print(f"[{datetime.now()}] Gemini REST error: {e}", flush=True)
            return None

    def get_recent_tweets(self, count=10):
        """Fetches the most recent tweets from the authenticated user's timeline"""
        if not self.client:
            return []
        try:
            # Get authenticated user info to get the ID
            me = self.client.get_me()
            user_id = me.data.id
            
            # Fetch tweets
            response = self.client.get_users_tweets(id=user_id, max_results=count, tweet_fields=['created_at'])
            
            tweets = []
            if response.data:
                for tweet in response.data:
                    # Format time to KST or just string
                    created_at = tweet.created_at
                    if created_at:
                        # Convert to string and adjust for simpler display
                        time_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        time_str = "Recent"
                        
                    tweets.append({
                        "time": time_str,
                        "text": tweet.text
                    })
            return tweets
        except Exception as e:
            print(f"[{datetime.now()}] Error fetching tweets from X: {e}", flush=True)
            return []

    def post_tweet(self, mode="standard"):
        """Executes the automated briefing based on mode"""
        print(f"[{datetime.now()}] Starting Broadcast (Mode: {mode})...", flush=True)
        
        tweet_text = None
        if mode == "promo":
            tweet_text = self.generate_promo_tweet()
        elif mode == "kr_insight":
            market_data = self.fetch_realtime_market_data()
            tweet_text = self.generate_korean_market_insight(market_data)
        else:
            # Standard sassy English market briefing
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
                    f.write(f"[{datetime.now()}] MODE: {mode} | CONTENT: {tweet_text}\n")

                if self.client:
                    response = self.client.create_tweet(text=tweet_text)
                    print(f"[{datetime.now()}] BROADCAST SUCCESS! ID: {response.data['id']}", flush=True)
                    return True
                else:
                    print(f"[{datetime.now()}] SIMULATION SUCCESS: {tweet_text}", flush=True)
                    return True
            except Exception as e:
                 print(f"[{datetime.now()}] Dispatch FAILED: {e}", flush=True)
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Omni Alpha X Broadcaster")
    parser.add_argument("--mode", type=str, default="standard", choices=["standard", "promo", "kr_insight"], help="Tweet mode")
    args = parser.parse_args()
    
    agent = XMarketAgent()
    agent.post_tweet(mode=args.mode)
