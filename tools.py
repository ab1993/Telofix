import os
import subprocess
import requests
from langchain_core.tools import tool

@tool
def list_files(directory_path: str) -> str:
    """Lists all files in the given directory."""
    try:
        return "\n".join(os.listdir(directory_path))
    except Exception as e:
        return f"Error: {e}"

@tool
def read_file(file_path: str) -> str:
    """Reads the content of a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def write_file(file_path: str, content: str) -> str:
    """Writes new content to a file. Overwrites existing content."""
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"

@tool
def run_maven_test(project_directory: str) -> str:
    """Runs the Maven test suite. You MUST pass the root directory of the Java project."""
    try:
        # cwd tells the subprocess to run inside the specific cloned workspace
        result = subprocess.run(
            ['mvn', 'test'],
            cwd=project_directory,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return "Tests Passed Successfully.\n" + result.stdout[-500:]
        else:
            return "Tests Failed.\n" + result.stdout[-1000:]
    except Exception as e:
        return f"Failed to execute Maven: {e}"

@tool
def push_changes_to_git(project_directory: str, branch_name: str, commit_message: str) -> str:
     """Pushes the modified code in the workspace back to the remote repository."""
     try:
         # 1. Add all changes
         subprocess.run(["git", "add", "."], cwd=project_directory, check=True)

         # 2. Commit
         subprocess.run(["git", "commit", "-m", commit_message], cwd=project_directory, check=True)

         # 3. Push to origin
         subprocess.run(["git", "push", "origin", branch_name], cwd=project_directory, check=True)

         return f"Successfully pushed changes to branch {branch_name}"
     except Exception as e:
         return f"Error pushing to Git: {e}"

@tool
def create_github_pull_request(issue_key: str, branch_name: str, body: str) -> str:
    """Creates a Pull Request on GitHub for the pushed branch."""
    token = os.getenv("GIT_APP_PASSWORD")
    repo = os.getenv("TARGET_REPO_URL") # e.g., github.com/ab1993/Telofix.git
    username = os.getenv("GIT_USERNAME")

    if not token or not repo:
        return "Error: Missing GitHub credentials or repo URL in .env"

    # Extract 'owner/repo' from 'github.com/owner/repo.git'
    repo_path = repo.replace("github.com/", "").replace(".git", "")
    url = f"https://api.github.com/repos/{repo_path}/pulls"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "title": f"fix: {issue_key} - Automated AI Fix",
        "head": branch_name,                # The branch the AI created
        "base": os.getenv("TARGET_REPO_BRANCH", "main"), # The branch to merge into
        "body": body,
        "maintainer_can_modify": True
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            pr_url = response.json().get("html_url")
            return f"Successfully created PR: {pr_url}"
        else:
            return f"Failed to create PR: {response.text}"
    except Exception as e:
        return f"Error creating PR: {str(e)}"