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
    print("Error: virtuals-sdk not found or version mismatch. Please install it: pip install virtuals-sdk==0.1.6")
    exit()

load_dotenv()

# --- Config ---
# 1. Vercel URL (The Brain)
BRAIN_URL = "https://us-market-ai-analyst.vercel.app/api/acp/validator" 

# 2. Virtuals API Key (Set this in your .env file or replace VIR-XXXXX)
API_KEY = os.getenv("VIRTUALS_API_KEY") or "VIR-XXXXX"

# 3. Agent Details
AGENT_NAME = "Omni Validator"

def relay_to_brain(ticker: str) -> str:
    """Relays the request from Virtuals to the Vercel backend (Gemini)."""
    print(f"🔄 Relay: Auditing {ticker}...")
    try:
        payload = {
            "method": "validate",
            "params": {"ticker": ticker},
            "id": "bridge-job-" + str(int(time.time()))
        }
        resp = requests.post(BRAIN_URL, json=payload, timeout=25)
        if resp.status_code == 200:
            result = resp.json().get("value", {})
            return result.get("validation_report", "Scan complete but no report returned.")
        return f"Error from Brain Code {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"Bridge Connection Error: {str(e)}"

# --- SDK Wrapper for Function ---
def verify_market_data_executable(ticker: str):
    report = relay_to_brain(ticker)
    if "Error" in report:
        return FunctionResultStatus.FAILED, report, {}
    return FunctionResultStatus.DONE, report, {"status": "audited"}

# --- State Callbacks (Required by SDK) ---
def get_agent_state(function_result, current_state):
    return {"status": "monitoring", "last_audit": ticker if 'ticker' in locals() else "None"}

def get_worker_state(function_result, current_state):
    return {"audit_active": True}

# --- Define Agent Structure ---

# 1. Define the Function (Tool)
verify_fn = Function(
    fn_name="verify_market_data",
    fn_description="Performs a skeptical, data-driven audit for a specific ticker (e.g. BTC, NVDA).",
    args=[Argument(name="ticker", type="string", description="Ticker symbol to audit")],
    executable=verify_market_data_executable
)

# 2. Define the Worker Configuration
validator_worker_cfg = WorkerConfig(
    id="audit_worker",
    worker_description="Specializes in fact-checking, technical analysis, and risk assessment.",
    get_state_fn=get_worker_state,
    action_space=[verify_fn],
    instruction="Always be skeptical and prioritize data over sentiment."
)

# 3. Define the Agent
omni_validator = Agent(
    api_key=API_KEY,
    name=AGENT_NAME,
    agent_goal="Ensure data integrity and expose market risks in Alpha's reports.",
    agent_description="Autonomous market auditor of the Omni Matrix.",
    get_agent_state_fn=get_agent_state,
    workers=[validator_worker_cfg]
)

if __name__ == "__main__":
    if API_KEY == "VIR-XXXXX":
        print("❌ CRITICAL: Virtuals API Key is missing. Please set VIRTUALS_API_KEY in your .env file.")
    else:
        print(f"🚀 {AGENT_NAME} is connecting to Virtuals Protocol...")
        print(f"🔗 Linked Brain: {BRAIN_URL}")
        
        try:
            # Compile and Run
            omni_validator.compile()
            print("✅ Agent Compiled. Entering Matrix...")
            omni_validator.run()
        except KeyboardInterrupt:
            print("\n👋 Offline. Agent has left the matrix.")
        except Exception as e:
            print(f"❌ Runtime Error: {e}")
