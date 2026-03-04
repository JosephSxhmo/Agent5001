# Personalized GitHub Repository Agent

This is a CLI-based multi-agent AI tool that uses LLMs to review code changes, draft GitHub Issues/PRs, and improve existing ones. It requires human approval before enacting any changes on GitHub.

## Setup

1.  **Clone this repository** (or navigate to your working directory).
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set Environment Variables:**
    The agent uses `litellm` which supports OpenAI, Anthropic, Gemini, Ollama, etc. Export the key you intend to use. Export your GitHub token for API operations.
    ```bash
    export OPENAI_API_KEY="your_api_key_here"  # Or ANTHROPIC_API_KEY, GEMINI_API_KEY
    export GITHUB_TOKEN="your_personal_access_token_with_repo_scope"
    ```
    
    **To use Ollama Cloud:**
    Generate an API key at [ollama.com](https://ollama.com) and export it:
    ```bash
    export OLLAMA_API_KEY="your_ollama_api_key"
    export OLLAMA_API_BASE="https://ollama.com/api" # Optional: set if needed by litellm
    ```

## Usage

The CLI (`agent.py`) supports multiple subcommands mapping to required tasks. By default, it uses the `gpt-4o` model. You can override this using the `--model` flag (e.g., `--model ollama/llama3`).

### 1. Review Changes
Analyze a git diff to identify issues, categorize changes, and assess risk.

**Review local uncommitted changes/current branch against main:**
```bash
python agent.py review --base main
```

**Review a specific commit range:**
```bash
python agent.py review --range HEAD~3..HEAD
```

### 2. Draft and Create Issue or PR
Create a draft which includes problem description/summary, evidence/files affected, acceptance criteria/test plan, and risk level.

**From instructions:**
```bash
python agent.py draft issue --instruction "Add rate limiting to login endpoint"
python agent.py draft pr --instruction "Refactor duplicated pricing logic"
```

**From a previous review (using cached plan):**
```bash
python agent.py draft issue
```

### 3. Human Approval (Gatekeeper)
The Gatekeeper agent acts as a critic. It reviews drafts for unsupported claims, missing tests, and policy violations. It also enforces human approval. Drafts are **not** automatically pushed to GitHub. They are displayed for your review.

**Approve a pending draft (creates the resource on GitHub):**
```bash
python agent.py approve --yes
```

**Reject a pending draft (aborts safely):**
```bash
python agent.py approve --no
```

### 4. Improve Existing Issue or PR
Critique an existing GitHub item and propose an improved structured version.

**Improve an Issue:**
```bash
python agent.py improve issue --number 42
```

**Improve a PR:**
```bash
python agent.py improve pr --number 17
```

## Architecture

This project implements:
*   **Planning Pattern:** Structuring tasks before drafting.
*   **Tool Use Pattern:** Fetching real diffs (`git diff`) and real issues (`requests` to GitHub API).
*   **Reflection Pattern:** The Gatekeeper criticizes generated content to enforce quality.
*   **Multi-Agent Pattern:** Divided into logical roles: `Reviewer`, `Planner`, `Writer`, and `Gatekeeper`.
