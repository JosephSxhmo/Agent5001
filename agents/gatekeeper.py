import json
import os
from pydantic import BaseModel, Field
from typing import Optional, Any
from .llm import get_llm_response

class ReflectionVerdict(BaseModel):
    pass_validation: bool = Field(description="Whether the draft passes validation (True=PASS, False=FAIL)")
    reasoning: str = Field(description="Detailed reasoning for the verdict, highlighting any lacking areas.")

def reflect_on_draft(draft: Any, draft_type: str, model: str = "gpt-4o") -> ReflectionVerdict:
    """
    Acts as the Gatekeeper critic. Checks for unsupported claims, missing evidence,
    missing tests, and policy violations. Returns a ReflectionVerdict.
    """
    print(f"[Gatekeeper] Reflecting on generated {draft_type} draft...")
    
    system_prompt = (
        "You are the Gatekeeper Critic agent. Your job is to review proposed GitHub Issues and Pull Requests. "
        "You must ensure the draft is reasonable. Check for unsupported claims or completely missing context. "
        "However, do NOT fail the draft strictly due to formatting, minor redundancies, or slightly brief test plans, "
        "as long as it generally describes the code changes accurately. Default to passing (PASS) unless there is a severe "
        "policy violation or complete hallucination."
    )
    
    draft_json = draft.model_dump_json(indent=2)
    prompt = f"Draft Type: {draft_type}\n\nDraft Content:\n{draft_json}\n\nPlease provide your reflection verdict."
    
    verdict = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=ReflectionVerdict)
    
    status = "PASS" if verdict.pass_validation else "FAIL"
    print(f"[Gatekeeper] Reflection verdict: {status} – {verdict.reasoning}")
    
    # Save the reflection artifact (requirement)
    with open("reflection_artifact.json", "w") as f:
        json.dump(verdict.model_dump(), f, indent=2)
        
    return verdict

class PendingDraft(BaseModel):
    item_type: str = Field(description="Type of item (issue or pr)")
    title: str = Field(description="Draft title")
    body: str = Field(description="Formatted body content")
    
def save_pending_draft(draft: PendingDraft):
    """Saves a draft for human approval."""
    with open(".pending_draft.json", "w") as f:
        json.dump(draft.model_dump(), f, indent=2)
        
def load_pending_draft() -> Optional[PendingDraft]:
    """Loads a pending draft if it exists."""
    if os.path.exists(".pending_draft.json"):
        with open(".pending_draft.json", "r") as f:
            return PendingDraft(**json.load(f))
    return None

def clear_pending_draft():
    """Clears the pending draft."""
    if os.path.exists(".pending_draft.json"):
        os.remove(".pending_draft.json")

def gatekeeper_approve(approved: bool) -> bool:
    """
    Handles the final approval step. Does not perform the actual API call, 
    but coordinates the rejection.
    """
    if approved:
        print("[Gatekeeper] Creating resource on GitHub...")
        return True
    else:
        print("[Gatekeeper] Draft rejected. No changes made.")
        clear_pending_draft()
        from .planner import clear_plan
        clear_plan()
        return False
