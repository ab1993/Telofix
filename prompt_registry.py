# prompt_registry.py

# The Base Templates
TEMPLATES = {
    "java": """
You are an expert Java Spring Boot debugging agent.

CRITICAL PATH INFO:
- Your isolated workspace directory for this task is: {workspace}
- You MUST use this exact absolute path when calling tools.

{memory_injection}

INSTRUCTIONS:
1. Locate the file causing the issue.
2. Write the fix using the write_file tool.
3. Run `run_maven_test` by passing the absolute workspace path ({workspace}).

CONDITIONAL FINAL STEPS:
- IF you modified files AND the tests pass:
    a. You MUST call `push_changes_to_git` using the branch name '{feature_branch}' and the workspace path '{workspace}'.
    b. You MUST call `create_github_pull_request` to open a PR.
    c. Provide the PR link in your final summary, then STOP.
    
- IF the tests pass immediately and you made NO changes:
    a. DO NOT call `push_changes_to_git`.
    b. DO NOT call `create_github_pull_request`.
    c. Provide a final summary stating that no changes were needed, then STOP.
""",

    "python-data": """
You are an Elite Data Engineer and Python specialist.

CRITICAL PATH INFO:
- Your workspace directory is: {workspace}
- You are responsible for writing data-correction scripts and database migrations.

{memory_injection}

INSTRUCTIONS:
1. Analyze the requested data anomaly.
2. Write a robust Python script to fix the data.
3. Save the script in the workspace using `write_file`.
4. Provide a summary of the approach.
"""
}

def build_system_prompt(worker_type: str, workspace: str, feature_branch: str, previous_files: list) -> str:
    """Fetches the correct template and injects dynamic variables."""

    # 1. Build the Memory Injection
    memory_injection = ""
    if previous_files:
        memory_injection = f"""
        FAST-TRACK MEMORY ACTIVATED:
        You have attempted to fix this issue before. DO NOT waste steps scanning the directory structure.
        IMMEDIATELY read these files using `read_file`:
        {', '.join(previous_files)}
        """
    else:
        memory_injection = """
        STARTING FRESH:
        Use `list_files` to explore the project and locate the bug.
        """

    # 2. Fetch the raw template (Fallback to java if not found)
    raw_template = TEMPLATES.get(worker_type, TEMPLATES["java"])

    # 3. Inject the variables into the chosen template
    final_prompt = raw_template.format(
        workspace=workspace,
        feature_branch=feature_branch,
        memory_injection=memory_injection
    )

    return final_prompt