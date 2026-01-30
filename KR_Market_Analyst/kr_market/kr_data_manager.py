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
        """KOSPI 200 및 KOSDAQ 150 종목 중 시가총액 상위 리스트 수집"""
        try:
            # 코스피 200 및 코스닥 150 리스트 가져오기
            kospi_200 = fdr.StockListing('KOSPI') # 실제로는 전체 리스트에서 필터링하거나 전용 티커 사용
            kosdaq_150 = fdr.StockListing('KOSDAQ')
            
            # 시가총액 기반 정렬 및 상위 종목 추출 (KOSPI 200의 상위 100개, KOSDAQ 150의 상위 100개 혼합)
            # 여기서는 단순화를 위해 각 시장의 상위 50개씩 우선 수집 (성능 고려)
            ks_top = kospi_200.sort_values(by='Marcap', ascending=False).head(50)
            kq_top = kosdaq_150.sort_values(by='Marcap', ascending=False).head(50)
            
            combined_list = []
            for _, row in ks_top.iterrows():
                combined_list.append((row['Code'], row['Name'], 'KOSPI'))
            for _, row in kq_top.iterrows():
                combined_list.append((row['Code'], row['Name'], 'KOSDAQ'))
                
            stock_data = []
            # 상위 100개 종목에 대해 상세 데이터 수집 (충분한 데이터 확보를 위함)
            for symbol, name, market in combined_list[:100]:
                try:
                    df = fdr.DataReader(symbol)
                    if not df.empty and len(df) >= 2:
                        last_price = df.iloc[-1]['Close']
                        prev_price = df.iloc[-2]['Close']
                        change_pct = ((last_price - prev_price) / prev_price) * 100
                        stock_data.append({
                            'symbol': symbol,
                            'name': name,
                            'price': f"{int(last_price):,}",
                            'change_pct': f"{change_pct:+.2f}%",
                            'market': market
                        })
                except:
                    continue
            return stock_data
        except Exception as e:
            print(f"Error fetching top stocks: {e}")
            # Fallback to hardcoded list if API fails
            return [
                {'symbol': '005930', 'name': '삼성전자', 'price': '72,000', 'change_pct': '+0.00%', 'market': 'KOSPI'},
                {'symbol': '000660', 'name': 'SK하이닉스', 'price': '180,000', 'change_pct': '+0.00%', 'market': 'KOSPI'}
            ]

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
