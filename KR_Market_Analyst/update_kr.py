import os
import subprocess
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_update():
    logger.info("🇰🇷 Starting KR Market Update Pipeline...")
    
    # 1. Collect Data
    logger.info("1/2 Collecting KR Market Data...")
    try:
        subprocess.run([sys.executable, "kr_market/kr_data_manager.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Data collection failed: {e}")
        return

    # 2. Generate AI Report
    logger.info("2/2 Generating AI Report...")
    try:
        subprocess.run([sys.executable, "kr_market/kr_report_generator.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ AI Report generation failed: {e}")
        return

    logger.info("✅ KR Market Update Completed successfully!")

if __name__ == "__main__":
    run_update()
