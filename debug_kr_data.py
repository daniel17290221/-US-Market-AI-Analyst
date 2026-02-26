from KR_Market_Analyst.kr_market.kr_data_manager import KRDataManager
import os

manager = KRDataManager()
print("Initialized manager")

print("1. Testing get_indices")
print(manager.get_indices())

print("2. Testing get_commodities")
print(manager.get_commodities())

print("3. Testing get_top_lists")
print(manager.get_top_lists())

print("4. Testing get_sector_performance")
print(manager.get_sector_performance())

print("5. Testing get_ipo_and_schedules")
print(manager.get_ipo_and_schedules())

print("6. Testing get_market_news")
print(manager.get_market_news())

print("7. Testing get_investor_flows")
print(manager.get_investor_flows())

print("All individual tests done")
