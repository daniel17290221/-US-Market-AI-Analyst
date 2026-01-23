#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Smart Money Screener v2.0 - Simplified for deployment
Combines 6 factors: Volume, Institutional, Technical, Fundamental, Analyst, Relative Strength
"""

import os
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedSmartMoneyScreener:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'smart_money_picks_v2.csv')
        
    def load_data(self) -> bool:
        try:
            vol_file = os.path.join(self.data_dir, 'us_volume_analysis.csv')
            holdings_file = os.path.join(self.data_dir, 'us_13f_holdings.csv')
            
            if os.path.exists(vol_file):
                self.volume_df = pd.read_csv(vol_file)
                logger.info(f"✅ Loaded volume analysis: {len(self.volume_df)} stocks")
            else:
                logger.warning("⚠️ Volume analysis not found")
                return False
            
            if os.path.exists(holdings_file):
                self.holdings_df = pd.read_csv(holdings_file)
                logger.info(f"✅ Loaded 13F holdings: {len(self.holdings_df)} stocks")
            else:
                logger.warning("⚠️ 13F holdings not found")
                return False
            
            # Load SPY for relative strength
            spy = yf.Ticker("SPY")
            self.spy_data = spy.history(period="3mo")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            return False
    
    def calculate_composite_score(self, volume_score, inst_score) -> float:
        """Simplified scoring - expand based on Part 2 document"""
        # Basic weighting: 50% volume + 50% institutional
        composite = (volume_score * 0.5) + (inst_score * 0.5)
        return round(composite, 1)
    
    def run_screening(self, top_n: int = 50) -> pd.DataFrame:
        logger.info("🔍 Running Enhanced Smart Money Screening...")
        
        merged_df = pd.merge(
            self.volume_df,
            self.holdings_df,
            on='ticker',
            how='inner',
            suffixes=('_vol', '_inst')
        )
        
        results = []
        
        for idx, row in tqdm(merged_df.iterrows(), total=len(merged_df), desc="Screening"):
            ticker = row['ticker']
            
            # Calculate composite
            vol_score = row.get('supply_demand_score', 50)
            inst_score = row.get('institutional_score', 50)
            composite = self.calculate_composite_score(vol_score, inst_score)
            
            # Determine grade
            if composite >= 80: grade = "🔥 S급 (즉시 매수)"
            elif composite >= 70: grade = "🌟 A급 (적극 매수)"
            elif composite >= 60: grade = "📈 B급 (매수 고려)"
            else: grade = "📊 C급 (관망)"
            
            result = {
                'ticker': ticker,
                'name': row.get('name_vol', ticker),
                'composite_score': composite,
                'grade': grade,
                'sd_score': vol_score,
                'inst_score': inst_score,
                'current_price': 0  # Add price fetch if needed
            }
            results.append(result)
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('composite_score', ascending=False)
        results_df['rank'] = range(1, len(results_df) + 1)
        
        return results_df
    
    def run(self, top_n: int = 50) -> pd.DataFrame:
        logger.info("🚀 Starting Enhanced Smart Money Screener v2.0...")
        
        if not self.load_data():
            logger.error("❌ Failed to load data")
            return pd.DataFrame()
        
        results_df = self.run_screening(top_n)
        
        results_df.to_csv(self.output_file, index=False)
        logger.info(f"✅ Saved to {self.output_file}")
        
        return results_df


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='.')
    parser.add_argument('--top', type=int, default=20)
    args = parser.parse_args()
    
    screener = EnhancedSmartMoneyScreener(data_dir=args.dir)
    results = screener.run(top_n=args.top)
    
    if not results.empty:
        print(f"\n🔥 TOP {args.top} ENHANCED SMART MONEY PICKS")
        print(results[['rank', 'ticker', 'grade', 'composite_score']].head(args.top).to_string())

if __name__ == "__main__":
    main()
