# n8n Personalized GitHub Agent 🤖

This directory contains the scaffolding to run the multi-agent architecture (Reviewer, Planner, Writer, Gatekeeper) entirely inside a locally hosted **n8n** instance.

## 1. Start n8n Locally
To keep your n8n data cleanly isolated to this project folder, I have created a startup script.

From this directory, simply run:
```bash
chmod +x start_n8n.sh
./start_n8n.sh
```
This will download and run the latest n8n instance using `npx`. Your browser will open at `http://localhost:5678`.

*Note: The first time you launch it, n8n will ask you to set up a local owner account.*

## 2. Import the Multi-Agent Workflow
Instead of building from scratch, I've scaffolded the Architecture into a JSON file:
1. In the n8n UI, go to **Workflows > "Add workflow"**.
2. Click the **`...`** menu in the top right corner and select **"Import from File"**.
3. Select `github_agent_workflow.json` from this folder.

### What is in the Workflow?
- **Chat Trigger:** The UI where you type your instructions (e.g. *"Review the latest commit"*).
- **Planner (AI Agent Node):** The orchestrator. It uses an LLM to decide what to do.
- **Ollama Node:** Drives the Planner using your local Llama3 model.
- **Tools (Reviewer & Gatekeeper):** Custom blocks attached to the Planner allowing it to run `git diff` locally, format PR drafts, and enforce strict Gatekeeper reflection criteria!
- **GitHub Node:** The execution step that actually creates the PR.

## 3. Configure Your Credentials
Before testing the Chat, you need to configure two things:

### A. Ollama (Local LLM)
1. Double-click the **"Ollama Chat Model"** node.
2. Under "Credential for Ollama API", click to create a new one.
3. Use the Base URL: `http://localhost:11434` (the default port for Ollama).
4. Save the credential. Make sure `llama3` is selected as the Model name.

### B. GitHub Personal Access Token
1. Double-click the **"GitHub (Create PR)"** node.
2. Under Credentials, create a new "GitHub API" token.
3. Paste your GitHub Personal Access Token (PAT) from earlier.
4. Update the "Repository" field inside the node from `JosephSxhmo/Agent5001` to whichever repo you want to test on.

## 4. Test the Agent!
At the bottom of the n8n editor, click the blue **"Chat"** button! 
Type: *"I just modified agent.py. Review my changes and draft a PR."*

n8n will show you the exact multi-agent reasoning steps (Reviewing -> Drafting -> Gatekeeping) right in the UI!
