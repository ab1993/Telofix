import sys
import os
import requests
from requests.auth import HTTPBasicAuth
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# --- THE CRITICAL IMPORTS ---
from tools import list_files, read_file, write_file, run_maven_test
tools = [list_files, read_file, write_file, run_maven_test]

# Loads your API keys into the background process
load_dotenv()
# ----------------------------

# 1. Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 2. Jira Update Function
def update_jira_ticket(issue_key, final_summary):
    domain = os.getenv("JIRA_DOMAIN")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not domain or not token:
        print("⚠️ Jira credentials missing. Skipping Jira update.")
        return

    auth = HTTPBasicAuth(email, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    print(f"\n📡 Pushing fix summary back to Jira ticket {issue_key}...")

    # Post Comment
    comment_url = f"https://{domain}/rest/api/2/issue/{issue_key}/comment"
    payload = {"body": f"✅ **AI Agent Fix Applied**\n\n{final_summary}"}
    requests.post(comment_url, json=payload, headers=headers, auth=auth)

    # Transition to Done
    transitions_url = f"https://{domain}/rest/api/2/issue/{issue_key}/transitions"
    response = requests.get(transitions_url, headers=headers, auth=auth).json()

    done_id = None
    for t in response.get("transitions", []):
        if "done" in t["name"].lower() or "resolved" in t["name"].lower():
            done_id = t["id"]
            break

    if done_id:
        requests.post(transitions_url, json={"transition": {"id": done_id}}, headers=headers, auth=auth)
        print("✅ Ticket successfully transitioned to Done.")
    else:
        print("⚠️ Could not find a 'Done' or 'Resolved' transition status for this ticket.")

# 3. Execution Entry Point (Called by server.py or CLI)
def run_agent(issue_key: str):
    print(f"🤖 Agent received automated task for {issue_key}")
    print("-" * 50)

    # STRICT SYSTEM PROMPT
    system_prompt = """
    You are an expert Java Spring Boot debugging agent.

    CRITICAL PATH INFO:
    - Your current working directory is the project root.
    - All Java source files are located under: src/main/java/
    - All Test files are located under: src/test/java/

    DEMO MODE INSTRUCTIONS:
    1. Locate `UserController.java` (usually in src/main/java/org/agilonhealth/agenticbugresolvertool/controller/).
    2. Add `@Autowired` to the `userRepo` field.
    3. Run `run_maven_test`.
    4. Once tests pass, provide a clean, executive summary in this format:
       'I have resolved the NullPointerException in UserController.java.
        Fix: Applied @Autowired to the userRepo dependency to ensure proper Spring injection.
        Verification: Maven tests passed successfully.'

    DO NOT mention directory errors, environmental issues, or your thought process in the final summary.

    CRITICAL RULE: If the Maven tests pass, YOUR JOB IS DONE. Immediately stop.
    """

    # Create the Agent inside the function so it uses the prompt
    agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

    # We set a default instruction for the user input
    user_input = "Fix the bug.\n\nIMPORTANT: Once tests pass, output a clean summary of what files you changed and exactly what code you fixed, then STOP."

    final_ai_message = ""

    # Run the agent loop
    for chunk in agent_executor.stream(
        {"messages": [("user", user_input)]},
        config={"recursion_limit": 50}, # Lowered limit to prevent runaway loops
        stream_mode="values"
    ):
        message = chunk["messages"][-1]
        message.pretty_print()

        if hasattr(message, 'content') and message.content:
             final_ai_message = message.content

    # The loop finished. Update Jira
    update_jira_ticket(issue_key, final_ai_message)

# 4. CLI Fallback (Allows running from terminal without the web server)
if __name__ == "__main__":
    issue_key = sys.argv[1] if len(sys.argv) > 1 else "TEST-123"
    run_agent(issue_key)