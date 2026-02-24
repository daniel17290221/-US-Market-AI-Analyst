import os
import threading
import time
from api.index import app
from agent_x_poster import XMarketAgent

def run_agent_loop():
    """Background loop for the AI Agent"""
    print("AI Agent Background Worker started.")
    agent = XMarketAgent()
    while True:
        try:
            # Post a market update
            agent.post_tweet()
        except Exception as e:
            print(f"Agent Loop Error: {e}")
        
        # Wait for 4 hours before the next update (14400 seconds)
        # You can adjust this frequency as needed
        print("Agent sleeping for 4 hours...")
        time.sleep(14400)

if __name__ == '__main__':
    # Start the AI Agent thread
    agent_thread = threading.Thread(target=run_agent_loop, daemon=True)
    agent_thread.start()
    
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting US Market Analyst Dashboard on port {port}...")
    app.run(host='0.0.0.0', port=port)
