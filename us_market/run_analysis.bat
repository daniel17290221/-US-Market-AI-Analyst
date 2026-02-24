@echo off
echo ========================================
echo US Market Analysis System
echo ========================================
echo.
echo Starting data collection and analysis...
echo This may take 10-15 minutes on first run.
echo.

python update_all.py

echo.
echo ========================================
echo Analysis Complete!
echo ========================================
echo.
echo Generated files:
echo - us_daily_prices.csv
echo - smart_money_picks_v2.csv
echo - us_macro_analysis.json
echo - sector_heatmap.json
echo.
echo To view results, run: python ..\flask_app.py
echo Then visit: http://localhost:5000
echo.
pause
