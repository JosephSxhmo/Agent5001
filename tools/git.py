import subprocess
import os
from typing import Optional

def run_git_command(args: list[str], cwd: Optional[str] = None) -> str:
    """Run a git command and return its output as a string.
    Raises subprocess.CalledProcessError on failure.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[Tool] Error running git command: {e.cmd}")
        print(f"[Tool] Stderr: {e.stderr}")
        raise

def get_git_diff(base: Optional[str] = None, commit_range: Optional[str] = None, cwd: Optional[str] = None) -> str:
    """
    Get the git diff.
    If commit_range is provided (e.g., HEAD~3..HEAD), it uses that.
    If base is provided, it compares the working tree or index to the base.
    Otherwise, it shows uncommitted changes.
    """
    args = ["diff"]
    
    if commit_range:
        args.append(commit_range)
    elif base:
        args.append(base)
    
    return run_git_command(args, cwd=cwd)

def get_current_branch(cwd: Optional[str] = None) -> str:
    """Returns the name of the current git branch."""
    return run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)

def read_file_content(filepath: str) -> str:
    """Reads the content of a file."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"[Tool] Error reading file {filepath}: {e}")
        return ""
