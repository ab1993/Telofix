import sys
import os
import requests
import shutil
from requests.auth import HTTPBasicAuth
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# NEW: Import the git manager we just created
from git_manager import setup_workspace

# --- THE CRITICAL IMPORTS ---
from tools import list_files, read_file, write_file, run_maven_test, push_changes_to_git, create_github_pull_request
tools = [list_files, read_file, write_file, run_maven_test, push_changes_to_git, create_github_pull_request]

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
def run_agent(issue_key: str):
    # Initialize variables at the top level
    abs_workspace = None
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    final_ai_message = "Agent failed to complete the task."

    try:
        # 1. Setup Workspace
        target_repo = os.getenv("TARGET_REPO_URL")
        workspace_dir = setup_workspace(issue_key, target_repo)
        abs_workspace = os.path.abspath(workspace_dir)
        print(f"📁 Workspace initialized at: {abs_workspace}")

        feature_branch = f"feature/telofix-{issue_key}"

        # 2. Setup Agent (RESTORED ORIGINAL PROMPT)
        system_prompt = f"""
        You are an expert Java Spring Boot debugging agent.

        CRITICAL PATH INFO:
        - Your isolated workspace directory for this task is: {abs_workspace}
        - You MUST use this exact absolute path when calling `list_files`, `read_file`, `write_file`, and `run_maven_test`.
        - All Java source files are located under: {abs_workspace}/src/main/java/
        - All Test files are located under: {abs_workspace}/src/test/java/

        INSTRUCTIONS:
        1. Locate the file causing the issue.
        2. Write the fix using the write_file tool.
        3. Run `run_maven_test` by passing the absolute workspace path ({abs_workspace}).
        4. Once tests pass, provide a clean summary of the fix.
        4. CRITICAL: Once tests pass, you MUST call `push_changes_to_git` using the branch name '{feature_branch}' and the workspace path '{abs_workspace}'.
        5. After pushing, provide your final summary.
        6. MANDATORY FINAL STEP: Call `create_github_pull_request` to open a PR for your changes.
        7. Provide the PR link in your final summary.

        CRITICAL RULE: If the Maven tests pass, YOUR JOB IS DONE. Immediately stop.
        """

        agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

        # 3. Exhaust the Generator (The Loop)
        print(f"🚀 Starting AI reasoning for {issue_key}...")

        for chunk in agent_executor.stream(
                {"messages": [("user", f"Fix the bug for {issue_key}.")]},
                config={"recursion_limit": 50},
                stream_mode="values"
        ):
            message = chunk["messages"][-1]
            message.pretty_print()

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
        # Update Jira BEFORE deleting the files
        update_jira_ticket(issue_key, final_ai_message)

        # 4. FINAL CLEANUP
        if abs_workspace and os.path.exists(abs_workspace):
            if os.getenv("KEEP_WORKSPACE", "false").lower() != "true":
                print(f"🧹 [Cleanup] Task finished. Deleting: {abs_workspace}")
                shutil.rmtree(abs_workspace)

    return usage

# 4. CLI Fallback
if __name__ == "__main__":
    issue_key = sys.argv[1] if len(sys.argv) > 1 else "TEST-123"
    run_agent(issue_key)