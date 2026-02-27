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

# Essential Scripts for Daily Report
SCRIPTS = [
    'analyze_volume.py',           # Generates us_volume_analysis.csv
    'analyze_13f.py',              # Generates us_13f_holdings.csv
    'smart_money_screener_v2.py', # Required for Top Stocks Picks (uses above 2)
    'macro_analyzer.py',           # Required for AI Macro Analysis
    'daily_report_generator.py',  # Final HTML & AI writing
    '../omni_x_broadcaster.py'    # Signal to X/Virtuals Ecosystem
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
            # Set a 2 minutes timeout for each script to prevent hanging
            res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True, cwd=base_dir, timeout=120)
            if res.stdout: 
                print(res.stdout, flush=True) 
        except subprocess.TimeoutExpired:
            logger.error(f"⚠️ Timeout: {script} took too long (skipped)")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error running {script}!")
            if e.stdout: print(f"STDOUT: {e.stdout}", flush=True)
            if e.stderr: print(f"STDERR: {e.stderr}", flush=True)
            # Continue to next script even if one fails
            continue
    
    # 2. Run KR Market Update
    logger.info("Starting KR Market Update...")
    kr_update_script = os.path.join(root_dir, 'KR_Market_Analyst', 'update_kr.py')
    if os.path.exists(kr_update_script):
        try:
            res = subprocess.run([sys.executable, kr_update_script], capture_output=True, text=True, check=True, cwd=os.path.join(root_dir, 'KR_Market_Analyst'))
            logger.info(res.stdout)
            logger.info("KR Update Complete!")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ KR Market Update failed!")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
    else:
        logger.warning("KR Update script not found.")
            
    logger.info("Full Update Cycle Complete!")

if __name__ == "__main__":
    run_all()
