import os
import json
import requests
from dotenv import load_dotenv
from virtuals_sdk.game import Agent, Worker, Function  # Assuming virtuals-sdk is used
# Note: If virtuals_sdk is not found, you can install it via: pip install virtuals-sdk

load_dotenv()

# --- Config ---
BASE_URL = "https://your-vercel-app.vercel.app"  # Update with your actual Vercel URL
AI_KEY = os.getenv("GOOGLE_API_KEY")

# --- Functions ---

def fetch_analysis(ticker: str) -> str:
    """Gets a sassy market analysis for a given ticker from the Omni Alpha Matrix."""
    try:
        # We call our own ACP endpoint for consistent analysis
        url = f"{BASE_URL}/api/acp"
        payload = {
            "method": "market_analysis",
            "params": {"ticker": ticker}
        }
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("result", {}).get("message", "The Matrix is silent on this ticker.")
        return f"Error from Matrix API: {resp.status_code}"
    except Exception as e:
        return f"Matrix unreachable: {str(e)}"

def post_tweet(content: str) -> str:
    """Posts a message to X (Twitter) as Omni Alpha."""
    # Importing logic from agent_x_poster.py
    try:
        from agent_x_poster import XMarketAgent
        agent = XMarketAgent()
        success = agent.post_custom_tweet(content)
        return "Success: Posted to X" if success else "Failed to post to X"
    except Exception as e:
        return f"Failed to post to X: {str(e)}"

# --- G.A.M.E. Architecture Setup ---

# 1. Define Functions
market_fn = Function(
    fn_name="fetch_analysis",
    fn_description="Fetch real-time sassy market analysis for a ticker (e.g. BTC, NVDA).",
    args=[{"name": "ticker", "type": "string", "description": "The stock or crypto ticker."}],
    executable=fetch_analysis
)

twitter_fn = Function(
    fn_name="post_tweet",
    fn_description="Post a final analysis or update to X (Twitter).",
    args=[{"name": "content", "type": "string", "description": "The content to post."}],
    executable=post_tweet
)

# 2. Define Worker
market_worker = Worker(
    worker_name="Omni Analyst Worker",
    worker_description="Specializes in financial market analysis and social media broadcasting.",
    functions=[market_fn, twitter_fn]
)

# 3. Define the Agent (High-Level Planner)
omni_agent = Agent(
    agent_name="Omni Alpha ($OMNI)",
    agent_description="""
    You are Omni Alpha, the world's most advanced autonomous investment intelligence.
    You monitor the global US and KR markets 24/7.
    Your personality is sassy, sarcastic, and high-conviction (Elon Musk style).
    You solve the matrix while others are paper-handing.
    """,
    goal="Analyze market trends and keep your followers informed with the highest quality Alpha.",
    workers=[market_worker]
)

# --- Execution ---

if __name__ == "__main__":
    # This script can be run locally via OpenClaw or standalone.
    # To use with OpenClaw, you typically start the agent and it listens for tasks.
    print("Omni Alpha OpenClaw Agent Started...")
    # Example local interaction:
    # result = omni_agent.run("Analyze BTC and tell the world.")
    # print(result)
    
    # Simple loop for demonstration
    while True:
        user_input = input("Enter Task (or 'exit'): ")
        if user_input.lower() == 'exit': break
        
        print(f"Agent is thinking about: {user_input}")
        response = omni_agent.run(user_input)
        print(f"Agent Response: {response}")
