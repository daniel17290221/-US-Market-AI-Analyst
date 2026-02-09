import os
import subprocess
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_update():
    logger.info("Starting KR Market Update Pipeline...")
    
    # 1. Collect Data
    logger.info("1/2 Collecting KR Market Data...")
    try:
        res = subprocess.run([sys.executable, "kr_market/kr_data_manager.py"], capture_output=True, text=True, check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        logger.info(res.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Data collection failed!")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return

    # 2. Generate AI Report
    logger.info("2/2 Generating AI Report...")
    try:
        res = subprocess.run([sys.executable, "kr_market/kr_report_generator.py"], capture_output=True, text=True, check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        logger.info(res.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ AI Report generation failed!")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return

    logger.info("KR Market Update Completed successfully!")

if __name__ == "__main__":
    run_update()
