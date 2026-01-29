import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
import os
import json

class KRDataManager:
    def __init__(self, output_dir='kr_market'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_market_indices(self):
        """KOSPI, KOSDAQ 지수 정보 수집"""
        indices = {
            'KS11': 'KOSPI',
            'KQ11': 'KOSDAQ',
            'KS200': 'KOSPI 200'
        }
        result = {}
        for ticker, name in indices.items():
            df = fdr.DataReader(ticker)
            if not df.empty:
                last_price = df.iloc[-1]['Close']
                prev_price = df.iloc[-2]['Close']
                change = last_price - prev_price
                change_pct = (change / prev_price) * 100
                result[ticker] = {
                    'name': name,
                    'price': f"{last_price:,.2f}",
                    'change': f"{change:+.2f} ({change_pct:+.2f}%)"
                }
        return result

    def get_top_stocks(self):
        """기존 StockListing 호출 대신 주요 대형주 리스트 사용 (속도 최적화)"""
        top_tickers = [
            ('005930', '삼성전자'), ('000660', 'SK하이닉스'), ('373220', 'LG에너지솔루션'),
            ('207940', '삼성바이오로직스'), ('005380', '현대차'), ('068270', '셀트리온'),
            ('000270', '기아'), ('005490', 'POSCO홀딩스'), ('035420', 'NAVER'),
            ('035720', '카카오'), ('105560', 'KB금융'), ('055550', '신한지주')
        ]
        
        stock_data = []
        for symbol, name in top_tickers:
            try:
                df = fdr.DataReader(symbol)
                if not df.empty:
                    last_price = df.iloc[-1]['Close']
                    prev_price = df.iloc[-2]['Close']
                    change_pct = ((last_price - prev_price) / prev_price) * 100
                    stock_data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': f"{int(last_price):,}",
                        'change_pct': f"{change_pct:+.2f}%",
                        'marcap': "-" # Marcap required listing or extra fetch
                    })
            except:
                continue
        return stock_data

    def collect_all(self):
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'market_indices': self.get_market_indices(),
            'top_stocks': self.get_top_stocks(),
            'commodities': self.get_dummy_commodities() # Placeholder
        }
        
        output_path = os.path.join(self.output_dir, 'kr_daily_data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"KR Market data saved to {output_path}")
        return data

    def get_dummy_commodities(self):
        return [
            {'name': '원/달러 환율', 'price': '1,345.50', 'change': '+2.50'},
            {'name': 'WTI유', 'price': '75.20', 'change': '-0.15'},
            {'name': '금', 'price': '2,030.10', 'change': '+5.20'}
        ]

if __name__ == "__main__":
    manager = KRDataManager()
    manager.collect_all()
