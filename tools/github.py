import os
import requests
from typing import Optional, Dict, Any

def _get_headers() -> Dict[str, str]:
    """Get necessary headers for GitHub API authentication."""
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def get_issue(owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
    """Fetch an issue (or PR) from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.get(url, headers=_get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[Tool] Failed to fetch issue/PR: {response.status_code} {response.text}")
        return None

def create_issue(owner: str, repo: str, title: str, body: str) -> Optional[Dict[str, Any]]:
    """Create a new issue on GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data = {"title": title, "body": body}
    response = requests.post(url, headers=_get_headers(), json=data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"[Tool] Failed to create issue: {response.status_code} {response.text}")
        return None

def create_pull_request(owner: str, repo: str, title: str, body: str, head: str, base: str) -> Optional[Dict[str, Any]]:
    """Create a new pull request on GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    data = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
    response = requests.post(url, headers=_get_headers(), json=data)
    if response.status_code == 201:
        return response.json()
    else:
        print(f"[Tool] Failed to create pull request: {response.status_code} {response.text}")
        return None
