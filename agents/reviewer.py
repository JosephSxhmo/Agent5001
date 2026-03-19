import json
from pydantic import BaseModel, Field
from typing import List, Optional
from .llm import get_llm_response
from .message import AgentMessage

class ReviewIssue(BaseModel):
    description: str = Field(description="Description of the issue or improvement")
    evidence: str = Field(description="Evidence from the diff to support this")
    category: str = Field(description="Category (e.g., bugfix, feature, refactor, performance)")
    risk_level: str = Field(description="Risk level (low, medium, high)")

class ReviewResult(BaseModel):
    summary: str = Field(description="Overall summary of the review")
    issues: List[ReviewIssue] = Field(description="List of identified issues/improvements")
    suggested_action: str = Field(description="Suggested action (Create Issue, Create PR, or No action required)")
    justification: str = Field(description="Justification for the suggested action based on findings")

class CritiqueResult(BaseModel):
    missing_info: List[str] = Field(description="Unclear or missing information")
    vague_language: List[str] = Field(description="Instances of vague language")
    critique_summary: str = Field(description="Overall critique of the current item")

async def review_route(msg: AgentMessage, session, model: str) -> Optional[AgentMessage]:
    """A2A entrypoint for the Reviewer."""
    instruction = msg.instruction
    context = msg.context
    
    if instruction == "Review local code changes":
        print("[Reviewer (A2A)] Requesting git diff via MCP...")
        diff_res = await session.call_tool("mcp_get_git_diff", arguments={})
        diff = diff_res.content[0].text
        
        system_prompt = (
            "You are an expert Reviewer agent. Analyze the provided git diff, "
            "identify potential issues, categorize the changes, assess the risk level, "
            "and decide whether to create an Issue, a PR, or NO ACTION. "
            "You must justify your decision using specific evidence from the diff."
        )
        prompt = f"Here is the git diff to analyze:\n\n```diff\n{diff}\n```\n\nPlease provide a comprehensive structured review."
        
        print("[Reviewer (A2A)] Analyzing diff...")
        result = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=ReviewResult)
        
        print("\n--- Review Summary ---")
        print(result.summary)
        print(f"Suggested Action: {result.suggested_action}")
        print("----------------------\n")
        
        out_context = {
            "summary": result.summary,
            "justification": result.justification,
            "issues_found": [i.model_dump() for i in result.issues],
            "suggested_action": result.suggested_action
        }
        return AgentMessage(sender="reviewer", receiver="planner", instruction="Decide action from review", context=out_context)
        
    elif instruction == "Critique existing item":
        item_type = context.get("type", "issue")
        item_number = context.get("number")
        
        print(f"[Reviewer (A2A)] Requesting GitHub item #{item_number} via MCP...")
        try:
            gh_res = await session.call_tool("mcp_fetch_github_item", arguments={"owner": "JosephSxhmo", "repo": "Agent5001", "issue_number": item_number})
            gh_data = gh_res.content[0].text
            item_json = json.loads(gh_data)
        except Exception as e:
            print(f"[Reviewer (A2A)] Failed to fetch GitHub item: {e}")
            return None
            
        original_title = item_json.get("title", "")
        original_body = item_json.get("body", "")
        
        system_prompt = (
            f"You are an expert Reviewer agent. Critique an existing GitHub {item_type}. "
            "Identify unclear/missing info, vague language, and suggest improvements."
        )
        prompt = f"Title: {original_title}\n\nBody:\n{original_body}\n\nPlease analyze and critique this {item_type}."
        
        print(f"[Reviewer (A2A)] Critiquing existing {item_type}...")
        critique_res = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=CritiqueResult)
        
        print("\n--- Critique ---")
        for mi in critique_res.missing_info:
            print(f"- Missing: {mi}")
        print("----------------\n")
        
        out_context = {
            "type": item_type,
            "original_title": original_title,
            "original_body": original_body,
            "critique_summary": critique_res.critique_summary
        }
        return AgentMessage(sender="reviewer", receiver="writer", instruction="Improve existing draft", context=out_context)

    return None
