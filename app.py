import os
from api.index import app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting US Market Analyst Dashboard on port {port}...")
    app.run(host='0.0.0.0', port=port)
