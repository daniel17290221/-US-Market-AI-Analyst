
import os
import re

path = r'c:\Users\mjang\Downloads\Investment Vibecodinglab\templates\index.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update the internal last-update text in the HTML
    content = content.replace('업데이트: 2026. 01. 22', '업데이트: 2026. 01. 27')
    
    # Update the fallback data inside the script
    # We look for the applyFallbackData backupData array
    new_backup_data = """
            const backupData = [
                { rank: "01", ticker: "NVDA", name: "NVIDIA Corporation", sector: "Technology", score: 96.5, signal: "적극 매수", price: 143.00, change: 8.5 },
                { rank: "02", ticker: "TSLA", name: "Tesla, Inc.", sector: "Automotive", score: 92.0, signal: "적극 매수", price: 259.00, change: 3.2 },
                { rank: "03", ticker: "AAPL", name: "Apple Inc.", sector: "Technology", score: 89.0, signal: "적극 매수", price: 228.50, change: 1.3 },
                { rank: "04", ticker: "MSFT", name: "Microsoft Corp", sector: "Software", score: 83.0, signal: "적극 매수", price: 426.00, change: 1.0 },
                { rank: "05", ticker: "AMZN", name: "Amazon.com", sector: "Commerce", score: 79.0, signal: "매수", price: 189.00, change: 0.6 },
                { rank: "06", ticker: "META", name: "Meta Platforms", sector: "Technology", score: 78.0, signal: "매수", price: 586.00, change: 1.5 },
                { rank: "07", ticker: "GOOGL", name: "Alphabet Inc", sector: "Technology", score: 77.0, signal: "매수", price: 166.00, change: 0.1 },
                { rank: "08", ticker: "AVGO", "name": "Broadcom Inc", sector: "Semiconductors", score: 76.0, signal: "매수", price: 173.00, change: 2.2 },
                { rank: "09", ticker: "AMD", "name": "Advanced Micro", sector: "Semiconductors", score: 75.0, signal: "매수", price: 156.00, change: -2.2 },
                { rank: "10", ticker: "COST", "name": "Costco Wholesale", sector: "Retail", score: 74.0, signal: "관망", price: 913.00, change: 0.9 }
            ];
"""
    
    # Simple regex to replace the old backupData array
    # It might be tricky if it spans multiple lines.
    pattern = r'const backupData = \[[\s\S]*?\];'
    if re.search(pattern, content):
        content = re.sub(pattern, new_backup_data.strip(), content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Frontend fallback updated to Jan 27th.")

except Exception as e:
    print(f"ERROR: {e}")
