import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mcp.server.fastmcp import FastMCP
from tools.git import get_git_diff, get_current_branch, read_file_content
from tools.github import get_issue, create_issue, create_pull_request

# Initialize the FastMCP server
mcp = FastMCP("Agent5001-Tools")

@mcp.tool()
def mcp_get_git_diff(base: str = None, commit_range: str = None) -> str:
    """Get the git diff for the repository explicitly containing local changes."""
    diff_output = get_git_diff(base, commit_range, cwd="/home/joseph/five001/Agent5001")
    return diff_output if diff_output else "No code changes in working directory."

@mcp.tool()
def mcp_read_file(filepath: str) -> str:
    """Reads the content of a file given its local filepath."""
    return read_file_content(filepath)

@mcp.tool()
def mcp_get_current_git_branch() -> str:
    """Returns the name of the current git branch."""
    return get_current_branch(cwd="/home/joseph/five001/Agent5001")

@mcp.tool()
def mcp_fetch_github_item(owner: str, repo: str, issue_number: int) -> str:
    """Fetch an issue (or PR) from a GitHub repository."""
    res = get_issue(owner, repo, issue_number)
    return json.dumps(res) if res else "Failed to fetch issue."

@mcp.tool()
def mcp_post_github_issue(owner: str, repo: str, title: str, body: str) -> str:
    """Create a new issue on the specified GitHub repository."""
    res = create_issue(owner, repo, title, body)
    return json.dumps(res) if res else "Failed to create issue."

@mcp.tool()
def mcp_post_github_pull_request(owner: str, repo: str, title: str, body: str, head: str, base: str) -> str:
    """Create a new pull request on the specified GitHub repository."""
    res = create_pull_request(owner, repo, title, body, head, base)
    return json.dumps(res) if res else "Failed to create pull request."

if __name__ == "__main__":
    # Start the standard MCP stdio transport server
    mcp.run()
