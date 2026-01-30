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
    'ai_summary_generator.py',
    'daily_report_generator.py',
    # 'final_report_generator.py' (Optional)
]

def run_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Starting Full US Market Update... ({base_dir})")
    
    for script in SCRIPTS:
        script_path = os.path.join(base_dir, script)
        if not os.path.exists(script_path):
            logger.warning(f"[WARNING] Script not found: {script}")
            continue
            
        logger.info(f"Running {script}...")
        try:
            # Run the script with its directory as CWD
            subprocess.run([sys.executable, script_path], check=True, cwd=base_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"[ERROR] Error running {script}: {e}")
            
    logger.info("Update Complete!")

if __name__ == "__main__":
    run_all()
