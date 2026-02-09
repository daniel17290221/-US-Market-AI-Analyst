#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update All Orchestrator
Runs all analysis scripts in sequence
"""
import os
import sys
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

SCRIPTS = [
    # Part 1: Data Collection
    'create_us_daily_prices.py',
    'analyze_volume.py',
    'analyze_13f.py',
    'analyze_etf_flows.py',
    
    # Part 2: Analysis
    'sector_heatmap.py',
    'options_flow.py',
    'insider_tracker.py',
    'portfolio_risk.py',
    'smart_money_screener_v2.py',
    
    # Part 3: AI & Reporting
    'macro_analyzer.py',
    'economic_calendar.py',
    'us_ai_analyzer.py',
    'ai_summary_generator.py',
    'daily_report_generator.py',
    # 'final_report_generator.py' (Optional)
]

def run_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir) # Root of the project
    logger.info(f"Starting Full Market Update... ({base_dir})")
    
    # 1. Run US Market Update
    for script in SCRIPTS:
        script_path = os.path.join(base_dir, script)
        if not os.path.exists(script_path):
            logger.warning(f"[WARNING] Script not found: {script}")
            continue
            
        logger.info(f"Running US script: {script}...")
        try:
            subprocess.run([sys.executable, script_path], check=True, cwd=base_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"[ERROR] Error running {script}: {e}")
    
    # 2. Run KR Market Update
    logger.info("Starting KR Market Update...")
    kr_update_script = os.path.join(root_dir, 'KR_Market_Analyst', 'update_kr.py')
    if os.path.exists(kr_update_script):
        try:
            subprocess.run([sys.executable, kr_update_script], check=True, cwd=os.path.join(root_dir, 'KR_Market_Analyst'))
            logger.info("KR Update Complete!")
        except Exception as e:
            logger.error(f"[ERROR] KR Market Update failed: {e}")
    else:
        logger.warning("KR Update script not found.")
            
    logger.info("Full Update Cycle Complete!")

if __name__ == "__main__":
    run_all()
