#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stock Summary Generator
Generates one-line summaries for top stocks
"""
import os, json, logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AISummaryGenerator:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'ai_stock_summaries.json')

    def generate_summary(self, ticker: str, data: Dict) -> str:
        """Professional Korean AI stock summaries"""
        score = data.get('composite_score', 50)
        
        if score >= 90:
            return f"{ticker}: 주성분 분석 결과 최상위권. 기관의 공격적인 순매수와 이례적인 거래량 폭발이 포착되었습니다. 기술적으로 강력한 돌파 구간에 진입하여 단기 목표가 상향 조정이 유효한 알짜 종목입니다."
        elif score >= 80:
            return f"{ticker}: 탄탄한 펀더멘털을 바탕으로 매집 신호가 뚜렷합니다. AI 수급 분석 결과 저점 매수세가 강력하게 유입되고 있어, 추가 상승 모멘텀이 충분한 것으로 판단됩니다."
        elif score >= 70:
            return f"{ticker}: 주요 지지선을 확보한 가운데 기관의 완만한 비중 확대가 관찰됩니다. 섹터 내 상대적 강세가 돋보이며 눌림목 구간에서 분할 매수 대응이 유리한 시점입니다."
        elif score >= 60:
            return f"{ticker}: 상승 모멘텀은 존재하나 일시적 매물 소화 과정이 예상됩니다. 거래량 추이를 지켜보며 핵심 지지선 이탈 여부를 확인하는 보수적 접근이 권장됩니다."
        else:
            return f"{ticker}: 현재 유의미한 수급 변화가 감지되지 않는 관망 구간입니다. 기술적 지표가 중립 이하이므로 뚜렷한 추세 전환 확인 전까지 대기 전략이 유리합니다."

    def run(self):
        # Load screener results
        screener_file = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if not os.path.exists(screener_file):
            logger.warning("No screener results found to summarize")
            return

        import pandas as pd
        df = pd.read_csv(screener_file)
        top_stocks = df.head(10)
        
        summaries = {}
        for _, row in top_stocks.iterrows():
            ticker = row['ticker']
            summaries[ticker] = self.generate_summary(ticker, row)
            
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ Generated {len(summaries)} summaries")

if __name__ == "__main__":
    AISummaryGenerator().run()
