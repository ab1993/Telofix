import os
import subprocess
from langchain_core.tools import tool

# Security Sandbox: Force all actions to happen inside the agentic-bug-resolver-tool folder
BASE_DIR = os.path.abspath("agentic-bug-resolver-tool")

@tool
def list_files(directory: str = ".") -> str:
    """Lists all files and directories in the specified directory. Defaults to current directory '.' if empty."""
    try:
        # If the agent passes an empty string or None, default to current directory
        path = directory if directory and directory.strip() else "."
        files = os.listdir(path)
        if not files:
            return f"Directory '{path}' is empty."
        return "\n".join(files)
    except Exception as e:
        return f"Error: {e}. Try using '.' to see the root directory."

@tool
def read_file(file_path: str) -> str:
    """Reads the contents of a file using a relative path from the project root."""
    try:
        # If the AI provides an absolute path that is doubled, we strip the redundant part
        clean_path = file_path.split("agentic-bug-resolver-tool/")[-1]

        with open(clean_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}. Please ensure you are using the relative path from the root (e.g., 'src/main/java/...')"

@tool
def write_file(file_path: str, content: str) -> str:
    """Writes content to a file using a relative path from the project root."""
    try:
        clean_path = file_path.split("agentic-bug-resolver-tool/")[-1]

        os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        with open(clean_path, 'w') as f:
            f.write(content)
        return f"Success: File '{clean_path}' has been updated."
    except Exception as e:
        return f"Error writing file: {e}"

@tool
def run_maven_test() -> str:
    """Compiles the Spring Boot project and runs tests. Returns the console logs."""
    try:
        # Auto-detect if Maven Wrapper is present, otherwise use global Maven
        if os.path.exists(os.path.join(BASE_DIR, "mvnw")):
            cmd = ["./mvnw", "test"]
        else:
            cmd = ["mvn", "test"]

        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=120 # Prevent the agent from getting stuck in an infinite build loop
        )

        output = result.stdout + "\n" + result.stderr

        # LLMs have context limits. We only return the last 2500 characters of the log
        # because the StackTrace and test failures are always at the bottom.
        if len(output) > 2500:
            return "...[Logs truncated]...\n" + output[-2500:]
        return output

    except subprocess.TimeoutExpired:
        return "Error: Maven test timed out after 120 seconds."
    except Exception as e:
        return f"Error running Maven: {str(e)}"