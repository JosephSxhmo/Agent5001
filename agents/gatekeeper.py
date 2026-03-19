import json
import os
from pydantic import BaseModel, Field
from typing import Optional, Any
from .llm import get_llm_response
from .message import AgentMessage

class ReflectionVerdict(BaseModel):
    pass_validation: bool = Field(description="Whether the draft passes validation (True=PASS, False=FAIL)")
    reasoning: str = Field(description="Detailed reasoning for the verdict, highlighting any lacking areas.")

class PendingDraft(BaseModel):
    item_type: str = Field(description="Type of item (issue or pr)")
    title: str = Field(description="Draft title")
    body: str = Field(description="Formatted body content")

def save_pending_draft(draft: PendingDraft):
    with open(".pending_draft.json", "w") as f:
        json.dump(draft.model_dump(), f, indent=2)
        
def load_pending_draft() -> Optional[PendingDraft]:
    if os.path.exists(".pending_draft.json"):
        with open(".pending_draft.json", "r") as f:
            return PendingDraft(**json.load(f))
    return None

def clear_pending_draft():
    if os.path.exists(".pending_draft.json"):
        os.remove(".pending_draft.json")

async def gatekeeper_route(msg: AgentMessage, session, model: str) -> Optional[AgentMessage]:
    """A2A entrypoint for the Gatekeeper."""
    instruction = msg.instruction
    context = msg.context
    
    if instruction == "Review generated draft":
        item_type = context.get("type", "issue")
        title = context.get("title", "")
        body = context.get("body", "")
        raw_draft_json = context.get("raw_draft_json", "{}")
        
        print(f"\\n--- DRAFT ({item_type.upper()}) ---")
        print(f"Title: {title}")
        print("Body:")
        print(body)
        print("-------------------\\n")
        
        print(f"[Gatekeeper (A2A)] Reflecting on generated {item_type} draft...")
        system_prompt = (
            "You are the Gatekeeper Critic agent. Your job is to review proposed GitHub Issues and Pull Requests. "
            "You must ensure the draft is high-quality. Fail the draft if you find unsupported claims, "
            "missing evidence/context, vague test plans, or general policy violations. Enforce strict standards."
        )
        prompt = f"Draft Type: {item_type}\\n\\nDraft Content:\\n{raw_draft_json}\\n\\nPlease provide your reflection verdict."
        
        verdict = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=ReflectionVerdict)
        
        status = "PASS" if verdict.pass_validation else "FAIL"
        print(f"[Gatekeeper (A2A)] Reflection verdict: {status} – {verdict.reasoning}")
        
        if verdict.pass_validation:
            print("[Gatekeeper (A2A)] Reflection verdict: PASS")
            pending = PendingDraft(item_type=item_type, title=title, body=body)
            save_pending_draft(pending)
            print("Action required: Run `venv/bin/python agent.py approve --yes` or `--no`")
            return AgentMessage(sender="gatekeeper", receiver="user", instruction="DONE")
        else:
            print("[Gatekeeper (A2A)] Reflection verdict: FAIL")
            print("Revision required before saving draft. Cycling back to Writer!")
            
            # Loop back to writer!
            out_context = {
                "type": item_type,
                "original_title": title,
                "original_body": body,
                "critique_summary": verdict.reasoning
            }
            return AgentMessage(sender="gatekeeper", receiver="writer", instruction="Improve existing draft", context=out_context)

    return None

async def gatekeeper_approve(approved: bool, session):
    """Handles manual approval step by contacting generic tools via MCP Session."""
    pending = load_pending_draft()
    if not pending:
        print("[Error] No pending drafts to approve.")
        return
        
    if approved:
        print("[Gatekeeper] Creating resource on GitHub via MCP Server...")
        if pending.item_type == "issue":
            res = await session.call_tool("mcp_post_github_issue", arguments={
                "owner": "JosephSxhmo",
                "repo": "Agent5001",
                "title": pending.title,
                "body": pending.body
            })
            print(f"[Tool] GitHub API Response: {res.content[0].text}")
        else:
            branch_res = await session.call_tool("mcp_get_current_git_branch", arguments={})
            head_branch = branch_res.content[0].text
            
            if not head_branch or head_branch == "HEAD":
                print("[Error] Cannot create PR from a detached HEAD or empty branch. Please checkout a named branch.")
                return
                
            res = await session.call_tool("mcp_post_github_pull_request", arguments={
                "owner": "JosephSxhmo",
                "repo": "Agent5001",
                "title": pending.title,
                "body": pending.body,
                "head": head_branch,
                "base": "main"
            })
            print(f"[Tool] GitHub API Response: {res.content[0].text}")
            
        clear_pending_draft()
    else:
        print("[Gatekeeper] Draft rejected. No changes made.")
        clear_pending_draft()
