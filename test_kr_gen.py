import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Mock KR_DATA_DIR
KR_DATA_DIR = os.path.join(BASE_DIR, 'KR_Market_Analyst')

def test_report_gen():
    try:
        from KR_Market_Analyst.kr_market.kr_report_generator import KRDailyReportGenerator
        data_dir = os.path.join(KR_DATA_DIR, 'kr_market')
        if not os.path.exists(os.path.join(data_dir, 'kr_daily_data.json')):
            print("Data file not found at default path, trying relatives...")
            data_dir = os.path.join(BASE_DIR, 'KR_Market_Analyst', 'kr_market')
            
        print(f"Using data_dir: {data_dir}")
        generator = KRDailyReportGenerator(data_dir=data_dir)
        html = generator.run()
        if "<html>" in html:
            print("SUCCESS: HTML generated")
            print(f"HTML size: {len(html)}")
        else:
            print("FAILURE: HTML output invalid")
            print(html)
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_report_gen()
