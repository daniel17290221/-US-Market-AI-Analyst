import os
import sys
# Mock environment for Vercel
os.environ["GOOGLE_API_KEY"] = "mock_key"

from api.index import app
import json

client = app.test_client()
print("DEBUG: Fetching /api/kr/smart-money...")
response = client.get('/api/kr/smart-money')
print(f"DEBUG: Status Code: {response.status_code}")
if response.status_code == 200:
    data = json.loads(response.data)
    print(f"DEBUG: Leaders count: {len(data.get('leaders_kospi', []))}")
    print(f"DEBUG: Gainers count: {len(data.get('gainers', []))}")
else:
    print(f"DEBUG: Response data: {response.data.decode()}")
