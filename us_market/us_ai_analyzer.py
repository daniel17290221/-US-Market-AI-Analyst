#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Market AI Stock Analyzer
Generates SWOT, Insights, and Targets for top US stocks using Gemini
"""
import os
import json
import logging
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class USAIAnalyzer:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.screener_file = os.path.join(data_dir, 'smart_money_picks_v2.csv')
        self.output_file = os.path.join(data_dir, 'us_ai_analysis.json')
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model = None
        self.client = None
        
        if self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.client = None

    def run(self, top_n=30):
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in environment")
            return

        if not os.path.exists(self.screener_file):
            logger.error(f"Screener file not found: {self.screener_file}")
            return

        df = pd.read_csv(self.screener_file)
        top_stocks = df.head(15)
        
        all_symbols = []
        for _, row in top_stocks.iterrows():
            ticker = row['ticker']
            name = row.get('name', ticker)
            
            # Fetch real-time price for better AI context
            curr_price = 0
            try:
                t = yf.Ticker(ticker)
                curr_price = t.info.get('regularMarketPrice') or t.fast_info.get('last_price', 0)
                if curr_price == 0:
                    hist = t.history(period="1d")
                    if not hist.empty: curr_price = hist['Close'].iloc[-1]
            except Exception as e:
                logger.warning(f"Failed to fetch price for {ticker}: {e}")
            
            all_symbols.append({
                'symbol': ticker, 
                'name': name,
                'price': round(curr_price, 2)
            })

        logger.info(f"Analyzing {len(all_symbols)} US stocks in batches...")
        
        results_map = {}
        # Load existing if possible to avoid redundant calls
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    results_map = json.load(f)
            except: pass

        chunk_size = 10 # Smaller for US due to potentially more complex data
        for i in range(0, len(all_symbols), chunk_size):
            batch = all_symbols[i:i + chunk_size]
            logger.info(f"Processing batch {i//chunk_size + 1}/{len(all_symbols)//chunk_size + 1}...")
            
            prompt = f"""
            당신은 미국 주식 전문 AI 분석가로서, 제공된 최신 시스템 가격(System Price)을 기준으로 정밀 분석을 수행해야 합니다.
            
            [분석 규칙]
            1. 제공된 'price'가 시스템 상의 기준 가격입니다. (액면분할 등이 반영된 최신 가격일 수 있음)
            2. 'dcf_target', 'dcf_bear', 'dcf_bull' 수치는 반드시 제공된 'price'와 수학적으로 호환되는 스케일이어야 합니다.
            3. 상승 여력(upside)은 (dcf_target - price) / price 로 계산하여 백분율로 표기하세요.
            4. 절대적으로 'price'와 동떨어진(예: 10배 차이 등) 목표가를 제시하지 마세요.
            
            [반드시 준수할 JSON 데이터 구조]
            각 티커(Ticker)를 키로 하는 객체를 반환하세요.
            {{
                "TICKER": {{
                    "insight": "핵심 투자 포인트 (1문장)",
                    "risk": "핵심 리스크 (1문장)",
                    "swot_s": "Strength 강점 키워드",
                    "swot_w": "Weakness 약점 키워드",
                    "swot_o": "Opportunity 기회 키워드",
                    "swot_t": "Threat 위협 키워드",
                    "mkt_cap": "시가총액 (예: $3.5T)",
                    "vol_ratio": "거래량 비율 (예: 1.5x ↑)",
                    "rsi": "RSI 지수 (예: 65.4)",
                    "upside": "+20%",
                    "dcf_target": "숫자",
                    "dcf_bear": "숫자", 
                    "dcf_bull": "숫자"
                }}
            }}

            [지시사항]
            1. 모든 텍스트는 한국어로 작성하세요.
            2. 정보가 부족하면 섹터 정보로 추론하세요.
            3. JSON 형식 외의 텍스트는 포함하지 마세요.
            
            [대상 종목]
            {json.dumps(batch, ensure_ascii=False)}
            """
            
            ai_text = ""
            try:
                for attempt in range(2):
                    try:
                        resp = self.model.generate_content(prompt)
                        ai_text = resp.text
                        if ai_text: break
                    except Exception as e:
                        logger.error(f"API Attempt {attempt+1} failed: {e}")
                        time.sleep(2)

                if ai_text:
                    cleaned = ai_text.replace('```json', '').replace('```', '').strip()
                    if '{' in cleaned and '}' in cleaned:
                        start = cleaned.find('{')
                        end = cleaned.rfind('}') + 1
                        cleaned = cleaned[start:end]
                    
                    batch_json = json.loads(cleaned)
                    # Normalize keys to uppercase
                    normalized_batch = {str(k).strip().upper(): v for k, v in batch_json.items()}
                    results_map.update(normalized_batch)
                    logger.info(f"Updated analysis for {len(normalized_batch)} stocks")
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
            
            time.sleep(1)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(results_map, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ US AI Analysis complete. Saved to {self.output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='.')
    args = parser.parse_args()
    
    analyzer = USAIAnalyzer(data_dir=args.dir)
    analyzer.run()
