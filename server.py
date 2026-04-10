import os
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
from dotenv import load_dotenv

# Import your actual agent logic
from agent import run_agent

# Load environment variables from .env
load_dotenv()

# Initialize the web server
app = FastAPI(title="Telofix Webhook Gateway")

# This dictionary replaces your Java ConcurrentHashMap for deduplication
active_tickets = {}

def execute_agent_loop(issue_key: str):
    print(f"\n🚀 [Telofix] Booting up agent for ticket: {issue_key}")
    try:
        run_agent(issue_key)
        # Only print success if run_agent didn't raise an exception
        print(f"✅ [Telofix] Agent finished processing {issue_key}")
    except Exception as e:
        print(f"❌ [Telofix] Agent crashed on {issue_key}: {str(e)}")
    finally:
        #redis_client.delete(f"telofix:lock:{issue_key}")
        print(f"🔓 [Telofix] Lock released for {issue_key}")

@app.post("/webhook/jira-trigger")
async def handle_jira_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receives the JSON payload from Jira when a ticket moves to the AI-Fix column."""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "Invalid or empty JSON payload"}

    # 1. Parse the Issue Key (Jira sends it nested in the 'issue' object)
    issue_key = payload.get("issue", {}).get("key")

    if not issue_key:
        return {"status": "ignored", "reason": "No issue key found in payload"}

    # 2. Deduplication check (Don't run if we are already fixing this ticket)
    if issue_key in active_tickets:
        print(f"⚠️ [Telofix] Ignoring duplicate webhook for {issue_key} - Agent already working.")
        return {"status": "ignored", "reason": f"Agent is already working on {issue_key}"}

    # 3. Mark as active and spin up the background task
    active_tickets[issue_key] = True
    background_tasks.add_task(execute_agent_loop, issue_key)

    print(f"📥 [Telofix] Webhook received. Dispatching agent for {issue_key}...")
    return {"status": "accepted", "message": f"Agent dispatched for {issue_key}"}

if __name__ == "__main__":
    print("🤖 Telofix Gateway is live and listening on port 8080...")
    # uvicorn is the high-performance server that runs FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8080)