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

# ==================================================================
# PRIORITY 1: FAST scripts that generate the HTML report quickly.
# These must complete within ~3 minutes so the report is always fresh.
# ==================================================================
FAST_SCRIPTS = [
    'macro_analyzer.py',           # ~10s - AI Macro Analysis from RSS
    'daily_report_generator.py',   # ~30s - HTML report (uses existing CSVs if present)
]

SLOW_SCRIPTS = [
    'create_us_daily_prices.py',   # 8 min - Full S&P500 download
    'analyze_volume.py',
    'analyze_13f.py',
    'smart_money_screener_v2.py',  # Depends on above CSVs - runs after download
    'us_ai_analyzer.py',
    '../omni_x_broadcaster.py'
]

TIMEOUTS = {
    'create_us_daily_prices.py': 480, # 8 minutes max
    'analyze_13f.py': 240,
    'us_ai_analyzer.py': 180,
    'macro_analyzer.py': 90,          # 90 seconds max for macro
    'daily_report_generator.py': 120, # 2 minutes max for report generation
    'smart_money_screener_v2.py': 60,
}

def run_scripts(script_list, base_dir, label=""):
    for script in script_list:
        script_path = os.path.join(base_dir, script)
        if not os.path.exists(script_path):
            logger.warning(f"[WARNING] Script not found: {script}")
            continue

        logger.info(f"Running {label} script: {script}...")
        try:
            start_time = datetime.now()
            timeout_sec = TIMEOUTS.get(script, 120)
            res = subprocess.run(
                [sys.executable, script_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, check=True, cwd=base_dir, timeout=timeout_sec
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ {script} completed in {duration:.1f}s")
            if res.stdout:
                print(res.stdout[:1500] + "..." if len(res.stdout) > 1500 else res.stdout, flush=True)
        except subprocess.TimeoutExpired:
            logger.error(f"⚠️ Timeout: {script} took too long (skipped)")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error running {script}!")
            if e.stdout: print(f"OUTPUT:\n{e.stdout}", flush=True)
            continue

def run_all():
    import argparse
    parser = argparse.ArgumentParser(description='Update All Orchestrator')
    parser.add_argument('--fast', action='store_true', help='Skip slow data collection scripts')
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)
    logger.info(f"Starting Full Market Update... ({base_dir})")

    # ★ PHASE 1: Run fast report-generation scripts FIRST
    logger.info("=== PHASE 1: Generating HTML Reports (Fast) ===")
    run_scripts(FAST_SCRIPTS, base_dir, label="FAST")

    # ★ PHASE 2: Run heavy data collection scripts AFTER report is saved
    if not args.fast:
        logger.info("=== PHASE 2: Heavy Data Collection (Slow) ===")
        run_scripts(SLOW_SCRIPTS, base_dir, label="SLOW")
    else:
        logger.info("=== PHASE 2: Skipping Heavy Data Collection (--fast mode) ===")

    logger.info("Full Update Cycle Complete!")

if __name__ == "__main__":
    run_all()
