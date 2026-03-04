import os
import sys

# Simulation of Vercel environment
API_DIR = os.path.join(os.getcwd(), 'api')
sys.path.append(API_DIR)
sys.path.append(os.getcwd())

print("Attempting to import all modules...")
try:
    import api.index as api_index
    print("SUCCESS: api.index imported")
    
    from api.routes.main import main_bp
    print("SUCCESS: routes.main imported")
    
    from api.routes.kr_market import kr_market_bp
    print("SUCCESS: routes.kr_market imported")
    
    from api.routes.us_market import us_market_bp
    print("SUCCESS: routes.us_market imported")
    
    from api.routes.omni import omni_bp
    print("SUCCESS: routes.omni imported")
    
    from api.routes.common import common_bp
    print("SUCCESS: routes.common imported")

    print("\nTesting BeautifulSoup with lxml...")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("<html><body>test</body></html>", "lxml")
    print("SUCCESS: BeautifulSoup with lxml works")

    print("\nAll tests successful!")
except Exception as e:
    print(f"\nFAILURE: {e}")
    import traceback
    traceback.print_exc()
