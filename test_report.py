
import os
import sys
from api.index import app

# Mock context for Flask
with app.test_request_context():
    from us_market.daily_report_generator import USDailyReportGenerator
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'us_market')
    
    print(f"Testing report generation with DATA_DIR: {DATA_DIR}")
    try:
        generator = USDailyReportGenerator(data_dir=DATA_DIR)
        html = generator.run()
        print(f"Generated HTML length: {len(html)}")
        if len(html) < 100:
            print("Generated HTML is suspiciously short:")
            print(html)
        else:
            print("HTML generated successfully (first 200 chars):")
            print(html[:200])
    except Exception as e:
        print(f"Error: {e}")
