import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'KR_Market_Analyst'))
from kr_market.kr_data_manager import KRDataManager
import json

print("Starting collection without AI...")
manager = KRDataManager(output_dir=os.getcwd()) # Save to root for now

# Manually trigger parts of collect_all except the AI part
print("Fetching lists...")
top_lists = manager.get_top_lists()
print("Fetching indices...")
market_indices = manager.get_indices()
print("Fetching commodities...")
commodities = manager.get_commodities()
print("Fetching sectors...")
sector_heatmap = manager.get_sector_performance()
print("Fetching ipo...")
ipo_news = manager.get_ipo_and_schedules()
print("Fetching news...")
market_news = manager.get_market_news()
print("Fetching flows...")
investor_flows = manager.get_investor_flows()

data = {
    'date': '2026-02-26 DEBUG',
    'market_indices': market_indices,
    'commodities': commodities,
    'sector_heatmap': sector_heatmap,
    'ipo_news': ipo_news,
    'market_news': market_news,
    'investor_flows': investor_flows,
    'top_stocks': top_lists['leaders_kospi'][:5], 
    'leaders_kospi': top_lists['leaders_kospi'],
    'leaders_kosdaq': top_lists['leaders_kosdaq'],
    'gainers': top_lists['gainers'],
    'volume': top_lists['volume'],
    'ai_analysis': {} 
}

with open('test_kr_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Data saved to test_kr_data.json")
