
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime
import os
import json
import traceback

class KRDataManager:
    def __init__(self, output_dir='KR_Market_Analyst/kr_market'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_real_market_movers(self, market_type='ALL'):
        """
        Fetch real-time market movers (Gainers, Volume) using FinanceDataReader.
        market_type: 'KOSPI', 'KOSDAQ', or 'ALL'
        """
        try:
            print(f"Fetching market data for {market_type}...")
            # For comprehensive rankings, we fetch the full listing
            # fdr.StockListing('KRX') returns KOSPI, KOSDAQ, KONEX
            df = fdr.StockListing('KRX')
            
            # Filter by market if needed
            if market_type == 'KOSPI':
                df = df[df['Market'] == 'KOSPI']
            elif market_type == 'KOSDAQ':
                df = df[df['Market'].isin(['KOSDAQ', 'KOSDAQ GLOBAL'])]

            # Ensure numeric columns
            df['ChagesRatio'] = pd.to_numeric(df['ChagesRatio'], errors='coerce')
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
            df['Marcap'] = pd.to_numeric(df['Marcap'], errors='coerce')
            
            # Remove minor stocks (penny stocks or low volume) to ensure quality data
            df = df[df['Volume'] > 0]
            
            return df
        except Exception as e:
            print(f"Error fetching real market movers: {e}")
            traceback.print_exc()
            return pd.DataFrame()

    def get_top_lists(self):
        """Generate formatted Top 10 lists for Gainers, Volume, and Leaders"""
        df = self.get_real_market_movers('ALL')
        
        if df.empty:
            return {
                'gainers': [],
                'volume': [],
                'market_cap': []
            }

        # 1. Top Gainers (High rank, decent volume to avoid noise)
        # Filter for volume > 100,000 to avoid liquidity traps
        gainers_df = df[df['Volume'] > 100000].sort_values(by='ChagesRatio', ascending=False).head(10)
        
        # 2. Top Volume
        volume_df = df.sort_values(by='Volume', ascending=False).head(10)
        
        # 3. Market Cap Leaders
        cap_df = df.sort_values(by='Marcap', ascending=False).head(10)

        def format_stocks(stock_df):
            result = []
            for _, row in stock_df.iterrows():
                try:
                    result.append({
                        'symbol': str(row['Code']),
                        'name': row['Name'],
                        'price': f"{int(row['Close']):,}",
                        'change': f"{row['ChagesRatio']:+.2f}",
                        'volume': f"{int(row['Volume']):,}",
                        'market': row['Market']
                    })
                except Exception as e:
                    continue
            return result

        return {
            'gainers': format_stocks(gainers_df),
            'volume': format_stocks(volume_df),
            'market_cap': format_stocks(cap_df)
        }

    def collect_all(self):
        """Main execution method to gather all data and save to JSON"""
        print("Starting KR Market Data Collection...")
        
        # 1. Get Top Lists
        top_lists = self.get_top_lists()
        
        # 2. Structure Data
        # We reuse 'top_stocks' key for the main dashboard list (using Market Cap leaders by default for the main table)
        # But we add specific keys for the tabs
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'top_stocks': top_lists['market_cap'], # Default view
            'gainers': top_lists['gainers'],
            'volume': top_lists['volume'],
            'leaders': top_lists['market_cap']
        }
        
        # Save
        output_path = os.path.join(self.output_dir, 'kr_daily_data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"KR Market data saved to {output_path}")
        return data

if __name__ == "__main__":
    manager = KRDataManager()
    manager.collect_all()
