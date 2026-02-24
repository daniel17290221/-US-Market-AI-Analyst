import os
import sys
import logging
from us_market.create_us_daily_prices import USStockDailyPricesCreator
from us_market.macro_analyzer import MacroAnalyzer
from us_market.daily_report_generator import USDailyReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_quick_test():
    """
    Runs a fast version of the full pipeline for testing.
    1. Fetches current prices for a few major tickers.
    2. Runs macro analysis.
    3. Generates the daily report.
    """
    logger.info("⚡ Starting US Market AI Quick Test...")
    
    # 1. Collect minimal data (Fast)
    logger.info("1/3 Collecting latest prices for key tickers...")
    price_creator = USStockDailyPricesCreator()
    # Override tickers to just a few for speed
    price_creator.get_sp500_tickers = lambda: [
        {'ticker': 'NVDA', 'name': 'NVIDIA', 'sector': 'Tech', 'market': 'S&P500'},
        {'ticker': 'TSLA', 'name': 'Tesla', 'sector': 'Auto', 'market': 'S&P500'},
        {'ticker': 'AAPL', 'name': 'Apple', 'sector': 'Tech', 'market': 'S&P500'},
        {'ticker': 'MSFT', 'name': 'Microsoft', 'sector': 'Tech', 'market': 'S&P500'}
    ]
    price_creator.run()
    
    # 2. Run Macro Analysis
    logger.info("2/3 Running AI Macro Analysis...")
    macro = MacroAnalyzer(data_dir='us_market')
    macro.run()
    
    # 3. Generate Daily Report
    logger.info("3/3 Generating Final HTML Report...")
    generator = USDailyReportGenerator(data_dir='us_market')
    report_html = generator.run()
    
    logger.info("✨ Quick Test Complete!")
    logger.info(f"📁 Report saved to: {generator.output_file}")
    
    try:
        print("\n" + "="*50)
        print("Success! Now check the 'Daily Report' tab in your dashboard.")
        print("성공! 이제 대시보드의 '데일리 리포트' 탭에서 새로고침을 누르세요.")
        print("="*50)
    except UnicodeEncodeError:
        print("\n" + "="*50)
        print("Success! Check the dashboard 'Daily Report' tab.")
        print("="*50)

if __name__ == "__main__":
    run_quick_test()
