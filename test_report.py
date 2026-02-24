
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
            print(f"Generated HTML is suspiciously short: {len(html)}")
        else:
            print(f"HTML generated successfully. Length: {len(html)}")
            # Avoid printing raw HTML to terminal which might cause charmap errors on Windows
            # print(html[:200]) 
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during report generation: {e}")
