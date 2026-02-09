import os
import sys

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from kr_data_manager import KRDataManager

if __name__ == "__main__":
    try:
        manager = KRDataManager()
        data = manager.collect_all()
        print("KR Market Data Update Completed Successfully.")
    except Exception as e:
        print(f"Update Failed: {e}")
