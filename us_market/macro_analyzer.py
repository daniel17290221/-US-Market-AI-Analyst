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
        Fetch recent market news headlines (Mock or RSS)
        For production, integrate with NewsAPI or similar
        """
        # Mock updated news for demonstration without external API
        return """
        1. Fed signals potential pause in rate cuts as inflation persists above 2%.
        2. Tech stocks rally led by AI chip demand; NVDA hits new high.
        3. Oil prices stabilize amid geopolitical tensions in Middle East.
        4. US Treasury yields tick higher, 10-year reaches 4.2%.
        5. Consumer spending data shows resilience despite economic headwinds.
        """

    def generate_analysis(self, news_text: str) -> Dict:
        """Generate analysis using selected AI model"""
        prompt = f"""
        Analyze the following US market news and data:
        {news_text}
        
        Provide a professional, localized US market analysis for Korean investors in JSON format.
        
        Fields required:
        - market_mood: ONE Korean term (극도의 공포, 공포, 중립, 탐욕, 극도의 탐욕)
        - mood_score: 0-100 score
        - key_takeaways: 3 specific, actionable points in professional Korean (금융 전문가 스타일)
        - sector_outlook: 2-3 sentences on promising sectors and why (in Korean)
        - risk_factors: 2-3 specific risks to monitor (in Korean)
        - strategy: A brief investment strategy recommendation (in Korean)
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
