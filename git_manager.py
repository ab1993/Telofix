import os
import subprocess
import shutil
from dotenv import load_dotenv

load_dotenv()

# We pull the specific Git provider settings from the .env
GIT_PROVIDER = os.getenv("GIT_PROVIDER", "github").lower()
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_APP_PASSWORD = os.getenv("GIT_APP_PASSWORD") # This is the PAT (Personal Access Token)

def get_clone_url(repo_url: str) -> str:
    """Injects the username and token securely into the Git URL for cloning."""
    if not GIT_USERNAME or not GIT_APP_PASSWORD:
        raise ValueError("Git credentials missing in .env")

    # Example repo_url input: "github.com/mycompany/myproject.git"
    # We strip https:// if the user accidentally included it
    clean_url = repo_url.replace("https://", "").replace("http://", "")

    # Construct the authenticated URL (works for GitHub, GitLab, and Bitbucket)
    return f"https://{GIT_USERNAME}:{GIT_APP_PASSWORD}@{clean_url}"

def setup_workspace(issue_key: str, repo_url: str) -> str:
    """Clones the repo, switches to the base branch, and creates a fix branch."""
    workspace_dir = f"./workspaces/{issue_key}"
    # Read the base branch from .env (default to main if not found)
    base_branch = os.getenv("TARGET_REPO_BRANCH", "main")

    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.makedirs(workspace_dir, exist_ok=True)

    print(f"📦 [Telofix Git] Cloning repository to {workspace_dir}...")
    auth_url = get_clone_url(repo_url)

    try:
        # 1. Clone only the specific base branch to save time/space
        subprocess.run(
            ["git", "clone", "-b", base_branch, auth_url, workspace_dir],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"🌿 [Telofix Git] Switched to base branch: {base_branch}")

        # 2. Create and checkout a new feature branch for the AI to work on
        feature_branch = f"feature/telofix-{issue_key}"
        print(f"🔨 [Telofix Git] Creating fix branch: {feature_branch}")
        subprocess.run(["git", "checkout", "-b", feature_branch], cwd=workspace_dir, check=True)

    except subprocess.CalledProcessError as e:
        print(f"❌ [Git Error]: {e.stderr}")
        raise RuntimeError(f"Git operation failed: {e.stderr}")

    return workspace_dir