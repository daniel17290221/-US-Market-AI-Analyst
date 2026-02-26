import requests

def test_key(key):
    print(f"Testing key: {key[:10]}...")
    url = "https://api.virtuals.io/api/accesses/tokens"
    headers = {"x-api-key": key}
    try:
        resp = requests.post(url, json={"data": {}}, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test the user's recent keys (from the user's message history and current file)
    keys = ["acp-bea3213a73ff63cabe80", "acp-ce6d38caabc1edd5f086"]
    for k in keys:
        test_key(k)
