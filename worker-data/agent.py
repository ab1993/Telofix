import sys
import os
import requests
import shutil
from requests.auth import HTTPBasicAuth
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from git_manager import setup_workspace
from prompt_registry import build_system_prompt

# --- THE CRITICAL IMPORTS ---
from tools import list_files, read_file, write_file, execute_python_script, push_changes_to_git, create_github_pull_request
tools = [list_files, read_file, write_file, execute_python_script, push_changes_to_git, create_github_pull_request]

load_dotenv()

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

    comment_url = f"https://{domain}/rest/api/2/issue/{issue_key}/comment"
    payload = {"body": f"✅ **AI Agent Fix Applied**\n\n{final_summary}"}
    requests.post(comment_url, json=payload, headers=headers, auth=auth)

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

# 3. Execution Entry Point
def run_agent(issue_key: str, worker_type: str = "java", previous_files: list = None):
    # Initialize variables at the top level
    abs_workspace = None
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    touched_files = set() # NEW: The memory tracker
    final_ai_message = "Agent failed to complete the task."

    # Make sure previous_files is a list
    if previous_files is None:
        previous_files = []

    try:
        # 1. Setup Workspace
        target_repo = os.getenv("TARGET_REPO_URL")
        workspace_dir = setup_workspace(issue_key, target_repo)
        abs_workspace = os.path.abspath(workspace_dir)
        print(f"📁 Workspace initialized at: {abs_workspace}")

        feature_branch = f"feature/telofix-{issue_key}"

        # 2. 🧠 Fetch the prompt dynamically in ONE line
        system_prompt = build_system_prompt(
            worker_type=worker_type,
            workspace=abs_workspace,
            feature_branch=feature_branch,
            previous_files=previous_files
        )

        agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

        # 3. Exhaust the Generator (The Loop)
        print(f"🚀 Starting AI reasoning for {issue_key}...")

        # In worker-data/agent.py, find the agent_executor.stream loop:
        for chunk in agent_executor.stream(
                # Change this line to force it to write a script:
                {"messages": [("user", f"Write a Python script called 'fix_data.py' in the workspace to deduplicate MongoDB users, and then execute it using the execute_python_script tool.")]},
                config={"recursion_limit": 50},
                stream_mode="values"
        ):
            message = chunk["messages"][-1]
            message.pretty_print()

            # NEW: Eavesdrop on tool calls to catch write_file events
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.get('name') == 'write_file':
                        file_path = tool_call.get('args', {}).get('file_path')
                        if file_path:
                            touched_files.add(file_path)

            # Capture tokens as we go
            if hasattr(message, 'usage_metadata') and message.usage_metadata:
                usage["prompt_tokens"] = message.usage_metadata.get("input_tokens", 0)
                usage["completion_tokens"] = message.usage_metadata.get("output_tokens", 0)

            if hasattr(message, 'content') and message.content:
                final_ai_message = message.content

        print(f"✅ AI finished reasoning for {issue_key}.")

    except Exception as e:
        print(f"❌ Execution Error: {e}")
        final_ai_message = f"Error: {str(e)}"

    finally:
        update_jira_ticket(issue_key, final_ai_message)

        # FINAL CLEANUP
        if abs_workspace and os.path.exists(abs_workspace):
            if os.getenv("KEEP_WORKSPACE", "false").lower() != "true":
                print(f"🧹 [Cleanup] Task finished. Deleting: {abs_workspace}")
                shutil.rmtree(abs_workspace)

    # NEW: Return both usage AND the memory of touched files
    return {
        "usage": usage,
        "touched_files": list(touched_files)
    }

# 4. CLI Fallback (Updated to match dictionary return)
if __name__ == "__main__":
    issue_key = sys.argv[1] if len(sys.argv) > 1 else "TEST-123"
    result = run_agent(issue_key)
    print("Final Result:", result)