import os
import json
import requests
import time
from dotenv import load_dotenv

# Virtuals SDK (Corrected for v0.1.6)
try:
    from virtuals_sdk.game.agent import Agent, WorkerConfig
    from virtuals_sdk.game.custom_types import Function, FunctionResultStatus, Argument
except ImportError:
    print("Error: virtuals-sdk not found. Please install it: pip install virtuals-sdk==0.1.6")
    exit()

load_dotenv()

# --- Config ---
BASE_URL = "https://us-market-ai-analyst.vercel.app" 
API_KEY = os.getenv("VIRTUALS_API_KEY") or "VIR-XXXXX"
AGENT_NAME = "Omni Alpha ($ALPHA)"

# --- Functions ---

def fetch_analysis(ticker: str):
    """Gets a sassy market analysis for a given ticker."""
    print(f"📡 Fetching Analysis for {ticker}...")
    try:
        url = f"{BASE_URL}/api/acp"
        payload = {
            "method": "market_analysis",
            "params": {"ticker": ticker},
            "id": "alpha-job-" + str(int(time.time()))
        }
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            # Return tuple for SDK: (status, feedback, info)
            report = data.get("value", {}).get("analysis_report", "The Matrix is silent.")
            return FunctionResultStatus.DONE, report, {"ticker": ticker}
        return FunctionResultStatus.FAILED, f"API Error: {resp.status_code}", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}

def post_tweet(content: str):
    """Posts a message to X (Twitter) as Omni Alpha."""
    print(f"🐦 Posting to X: {content[:30]}...")
    try:
        from agent_x_poster import XMarketAgent
        agent = XMarketAgent()
        success = agent.post_custom_tweet(content)
        if success:
            return FunctionResultStatus.DONE, "Success: Posted to X", {}
        return FunctionResultStatus.FAILED, "Twitter API Rejected request.", {}
    except Exception as e:
        return FunctionResultStatus.FAILED, str(e), {}

# --- State Callbacks (Required) ---
def get_agent_state(function_result, current_state):
    return {"status": "observing", "focus": "Global Alpha"}

def get_worker_state(function_result, current_state):
    return {"analysis_count": 0}

# --- G.A.M.E. Architecture Setup ---

# 1. Define Functions
market_fn = Function(
    fn_name="fetch_analysis",
    fn_description="Fetch real-time sassy market analysis for a ticker (e.g. BTC, NVDA).",
    args=[Argument(name="ticker", type="string", description="The stock or crypto ticker.")],
    executable=fetch_analysis
)

twitter_fn = Function(
    fn_name="post_tweet",
    fn_description="Post a final analysis or update to X (Twitter).",
    args=[Argument(name="content", type="string", description="The content to post.")],
    executable=post_tweet
)

# 2. Define Worker Configuration
analyst_worker_cfg = WorkerConfig(
    id="alpha_analyst",
    worker_description="Specializes in financial market analysis and social media broadcasting.",
    get_state_fn=get_worker_state,
    action_space=[market_fn, twitter_fn],
    instruction="Be sassy, Elon-style, and high-conviction."
)

# 3. Define the Agent
omni_alpha = Agent(
    api_key=API_KEY,
    name=AGENT_NAME,
    agent_goal="Analyze market trends and provide the highest quality Alpha.",
    agent_description="The world's most advanced autonomous investment intelligence.",
    get_agent_state_fn=get_agent_state,
    workers=[analyst_worker_cfg]
)

if __name__ == "__main__":
    if API_KEY == "VIR-XXXXX":
        print("❌ Virtuals API Key missing.")
    else:
        print(f"🚀 {AGENT_NAME} OpenClaw Agent Started...")
        omni_alpha.compile()
        omni_alpha.run()
