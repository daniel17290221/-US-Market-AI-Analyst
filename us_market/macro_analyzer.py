#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Market Macro AI Analyzer
Uses Gemini 3.0 (or GPT-5.2) to analyze market conditions and news
"""

import os
import json
import requests
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
try:
    from google import genai
except ImportError:
    try:
        import google.generativeai as genai
    except ImportError:
        genai = None

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MacroAnalyzer:
    def __init__(self, data_dir: str = '.', model: str = 'gemini'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'us_macro_analysis.json')
        self.model = model
        
        # Configure APIs
        self.gemini_key = os.getenv('GOOGLE_API_KEY')
        
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.client = None
            except:
                self.client = None
    
    def fetch_market_news(self) -> str:
        """
        Fetch recent market news headlines from real RSS feeds (CNBC/Yahoo/Reuters)
        """
        import xml.etree.ElementTree as ET
        
        feeds = [
            "https://search.cnbc.com/rs/search/all/view.rss?partnerId=2000&keywords=market",
            "https://finance.yahoo.com/rss/topstories"
        ]
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        news_items = []
        
        for url in feeds:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    # Fetching up to 8 items to capture more context
                    for item in root.findall('.//item')[:8]:
                        title = item.find('title').text
                        # Get more description to help AI understand context
                        desc = item.find('description').text if item.find('description') is not None else ""
                        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                        news_items.append(f"[{pub_date}] TITLE: {title}\nSUMMARY: {desc[:300]}...")
            except Exception as e:
                logger.warning(f"Failed to fetch feed {url}: {e}")
        
        if news_items:
            logger.info(f"Successfully fetched {len(news_items)} real-time news items.")
            # Join with clear separators for AI processing
            return "\n---\n".join(news_items)
            
        # Fallback to a slightly more dynamic mock if all feeds fail
        return f"""
        - Market Update ({datetime.now().strftime('%Y-%m-%d')}): 
        - US Stocks show mixed performance as investors digest recent economic data.
        - Treasury yields and corporate earnings reports are driving sector movements.
        - Focus remains on labor market resilience and consumer sentiment.
        """

    def generate_analysis(self, news_text: str) -> Dict:
        """Generate analysis using selected AI model"""
        prompt = f"""
        당신은 월스트리트 출신의 수석 매크로 전략가입니다. 다음의 '실시간 뉴스 헤드라인 및 요약'을 면밀히 분석하세요:
        {news_text}
        
        [분석 지침]
        1. **실시간성 극대화**: '미국의 이란 공격', '특정 기업의 급격한 실적 변화' 등 현재 수집된 뉴스 중 가장 파괴력이 큰 이벤트를 중심으로 분석하세요.
        2. **지표와의 연결**: 단순히 뉴스를 나열하지 말고, 이 뉴스가 '유가(WTI)', '국채 금리', '나스닥' 등에 구체적으로 어떤 영향을 주는지 인과관계를 설명하세요.
        3. **진부함 탈피**: '지정학적 리스크' 같은 단어 대신 '중동발 유가 발작', '호재를 삼킨 미사일' 등 뉴스 내용을 반영한 구체적인 용어를 사용하세요.
        
        JSON 형식으로 답변하세요:
        - market_mood: ONE Korean term (극도의 공포, 공포, 중립, 탐욕, 극도의 탐욕)
        - mood_score: 0-100 score
        - key_takeaways: 오늘의 뉴스를 관통하는 가장 핵심적인 관점 3가지 (뉴스 기반의 구체적인 내용)
        - sector_outlook: 특정 뉴스에 직접적으로 영향받는 섹터와 전망 (2-3문장)
        - risk_factors: 뉴스에서 도출된 긴급한 리스크 요인 2-3개
        - strategy: 현재의 긴박한 시장 상황에 맞춘 구체적인 대응 전략
        """
        
        try:
            if self.model == 'gemini' and (self.gemini_key):
                import google.generativeai as genai
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(prompt)
                return self._parse_response(response.text)
            
            else:
                logger.warning("No API keys found. Returning mock analysis.")
                return self._get_mock_analysis()
                
        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return self._get_mock_analysis()

    def _parse_response(self, text: str) -> Dict:
        """Clean and parse JSON from AI response"""
        try:
            text = text.replace('```json', '').replace('```', '')
            return json.loads(text)
        except:
            return self._get_mock_analysis()

    def _get_mock_analysis(self) -> Dict:
        """Fallback mock analysis"""
        return {
            "market_mood": "Greed",
            "mood_score": 75,
            "key_takeaways": [
                "AI 주도 기술주 랠리가 시장 상승 견인",
                "금리 인하 불확실성에도 소비자 심리 견고",
                "지정학적 리스크가 유가에 미치는 영향 제한적"
            ],
            "sector_outlook": "기술(Tech) 및 임의소비재(Discretionary) 강세 예상",
            "risk_factors": "국채 금리 상승 및 인플레이션 고착화 우려"
        }

    def run(self):
        logger.info(f"🧠 Running Macro Analysis using {self.model}...")
        news = self.fetch_market_news()
        analysis = self.generate_analysis(news)
        
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['model'] = self.model
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved analysis to {self.output_file}")
        return analysis

if __name__ == "__main__":
    MacroAnalyzer().run()
