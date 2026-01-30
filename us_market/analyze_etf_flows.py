#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF Fund Flow Analysis
Tracks 24 major ETFs with flow score calculation
"""

import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ETFFlowAnalyzer:
    """Analyze fund flows for major US ETFs"""
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'us_etf_flows.csv')
        
        # 24 Major ETFs to track
        self.etf_universe = {
            # Broad Market
            'SPY': {'name': 'SPDR S&P 500', 'category': 'Broad Market'},
            'QQQ': {'name': 'Invesco QQQ', 'category': 'Broad Market'},
            'IWM': {'name': 'Russell 2000', 'category': 'Broad Market'},
            'DIA': {'name': 'Dow Jones', 'category': 'Broad Market'},
            'VTI': {'name': 'Vanguard Total', 'category': 'Broad Market'},
            
            # Sector ETFs
            'XLK': {'name': 'Technology', 'category': 'Sector'},
            'XLF': {'name': 'Financials', 'category': 'Sector'},
            'XLV': {'name': 'Healthcare', 'category': 'Sector'},
            'XLE': {'name': 'Energy', 'category': 'Sector'},
            'XLY': {'name': 'Consumer Disc', 'category': 'Sector'},
            'XLP': {'name': 'Consumer Staples', 'category': 'Sector'},
            'XLI': {'name': 'Industrials', 'category': 'Sector'},
            'XLB': {'name': 'Materials', 'category': 'Sector'},
            'XLU': {'name': 'Utilities', 'category': 'Sector'},
            'XLRE': {'name': 'Real Estate', 'category': 'Sector'},
            'XLC': {'name': 'Comm Services', 'category': 'Sector'},
            
            # Commodities & Alternatives
            'GLD': {'name': 'Gold', 'category': 'Commodity'},
            'SLV': {'name': 'Silver', 'category': 'Commodity'},
            'USO': {'name': 'Oil', 'category': 'Commodity'},
            'TLT': {'name': '20Y+ Treasury', 'category': 'Fixed Income'},
            'HYG': {'name': 'High Yield', 'category': 'Fixed Income'},
            'LQD': {'name': 'Investment Grade', 'category': 'Fixed Income'},
            
            # International
            'EFA': {'name': 'Developed Markets', 'category': 'International'},
            'EEM': {'name': 'Emerging Markets', 'category': 'International'},
        }
        
    def calculate_flow_proxy(self, ticker: str) -> Dict:
        """
        Calculate flow score using OBV, volume ratio, and price momentum
        """
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period='3mo')
            
            if hist.empty or len(hist) < 20:
                return None
            
            # OBV Calculation
            obv = [0]
            for i in range(1, len(hist)):
                if hist['Close'].iloc[i] > hist['Close'].iloc[i-1]:
                    obv.append(obv[-1] + hist['Volume'].iloc[i])
                elif hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                    obv.append(obv[-1] - hist['Volume'].iloc[i])
                else:
                    obv.append(obv[-1])
            
            # Trend
            obv_20d_ago = obv[-20] if len(obv) > 20 else obv[0]
            obv_change = (obv[-1] - obv_20d_ago) / abs(obv_20d_ago) * 100 if obv_20d_ago != 0 else 0
            
            # Volume Ratio (5d vs 20d)
            vol_5d = hist['Volume'].tail(5).mean()
            vol_20d = hist['Volume'].tail(20).mean()
            vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1
            
            # Price Momentum (20d)
            price_change = hist['Close'].pct_change(20).iloc[-1] * 100
            
            # Flow Score (0-100)
            score = 50
            
            # OBV Contribution
            if obv_change > 20: score += 25
            elif obv_change > 10: score += 15
            elif obv_change < -20: score -= 25
            elif obv_change < -10: score -= 15
            
            # Volume Contribution
            if vol_ratio > 1.5: score += 15
            elif vol_ratio > 1.2: score += 10
            elif vol_ratio < 0.8: score -= 10
            
            # Price Contribution
            if price_change > 5: score += 10
            elif price_change < -5: score -= 10
            
            score = max(0, min(100, score))
            
            return {
                'ticker': ticker,
                'name': self.etf_universe[ticker]['name'],
                'category': self.etf_universe[ticker]['category'],
                'current_price': round(hist['Close'].iloc[-1], 2),
                'price_change_20d': round(price_change, 2),
                'vol_ratio_5d_20d': round(vol_ratio, 2),
                'obv_change_pct': round(obv_change, 2),
                'flow_score': round(score, 1)
            }
            
        except Exception as e:
            logger.warning(f"Failed to analyze {ticker}: {e}")
            return None
    
    def run(self) -> pd.DataFrame:
        """Analyze all ETFs"""
        logger.info("Starting ETF Flow Analysis...")
        
        results = []
        
        for ticker in self.etf_universe.keys():
            logger.info(f"Processing {ticker}...")
            analysis = self.calculate_flow_proxy(ticker)
            if analysis:
                results.append(analysis)
        
        results_df = pd.DataFrame(results)
        
        # Save CSV
        results_df.to_csv(self.output_file, index=False)
        logger.info(f"✅ Saved to {self.output_file}")
        
        # Summary
        logger.info("\n📊 Flow Summary:")
        logger.info(f"Strong Inflows (70+): {len(results_df[results_df['flow_score'] >= 70])}")
        logger.info(f"Moderate Inflows (55-70): {len(results_df[(results_df['flow_score'] >= 55) & (results_df['flow_score'] < 70)])}")
        logger.info(f"Neutral (45-55): {len(results_df[(results_df['flow_score'] >= 45) & (results_df['flow_score'] < 55)])}")
        logger.info(f"Outflows (<45): {len(results_df[results_df['flow_score'] < 45])}")
        
        return results_df


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='.')
    args = parser.parse_args()
    
    analyzer = ETFFlowAnalyzer(data_dir=args.dir)
    results = analyzer.run()
    
    print("\n[HOT] Top 5 Inflows:")
    print(results.nlargest(5, 'flow_score')[['ticker', 'name', 'flow_score', 'price_change_20d']])
    
    print("\n[COLD] Top 5 Outflows:")
    print(results.nsmallest(5, 'flow_score')[['ticker', 'name', 'flow_score', 'price_change_20d']])


if __name__ == "__main__":
    main()
