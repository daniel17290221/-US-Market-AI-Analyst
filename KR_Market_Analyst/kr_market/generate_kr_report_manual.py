
import os
import sys

# Ensure current dir is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from kr_report_generator import KRDailyReportGenerator

if __name__ == "__main__":
    print("Generating KR Daily Report Manually...")
    try:
        generator = KRDailyReportGenerator(data_dir=current_dir)
        result = generator.run()
        if result:
            print("Successfully generated report.")
        else:
            print("Failed to generate report (maybe no data found).")
    except Exception as e:
        print(f"Error: {e}")
