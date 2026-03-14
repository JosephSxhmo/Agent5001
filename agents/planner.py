import json
import os
from pydantic import BaseModel, Field
from typing import Optional
from .llm import get_llm_response

class PlanContext(BaseModel):
    action: str = Field(description="The action to take: 'issue' or 'pr'")
    context: str = Field(description="The context or instructions for the Writer to use")

def load_plan() -> Optional[PlanContext]:
    """Loads a saved plan if one exists."""
    if os.path.exists(".agent_plan.json"):
        with open(".agent_plan.json", "r") as f:
            data = json.load(f)
            return PlanContext(**data)
    return None

def save_plan(plan: PlanContext):
    """Saves the plan for later use."""
    with open(".agent_plan.json", "w") as f:
        json.dump(plan.model_dump(), f)

def clear_plan():
    """Clears the saved plan."""
    if os.path.exists(".agent_plan.json"):
        os.remove(".agent_plan.json")

def plan_from_review(review_result: any) -> PlanContext:
    """
    Translates a ReviewResult into a PlanContext.
    """
    print("[Planner] Deciding action based on review...")
    
    action = "none"
    suggested = review_result.suggested_action.lower()
    
    if "no action" in suggested or "none" in suggested:
        action = "none"
    elif "issue" in suggested:
        action = "issue"
    elif "pr" in suggested or "pull request" in suggested:
        action = "pr"
        
    context_data = {
        "summary": review_result.summary,
        "justification": review_result.justification,
        "issues_found": [i.model_dump() for i in review_result.issues]
    }
    
    return PlanContext(action=action, context=json.dumps(context_data, indent=2))

class InstructionValidation(BaseModel):
    is_valid: bool = Field(description="Whether the instruction is valid and in scope")
    reasoning: str = Field(description="Reasoning for validation result")
    inferred_action: str = Field(description="Inferred action: 'issue' or 'pr'")

def plan_from_instruction(instruction: str, requested_type: str, model: str = "gpt-4o") -> Optional[PlanContext]:
    """
    Validates user instruction and creates a PlanContext.
    """
    print(f"[Planner] Validating instruction for {requested_type}...")
    
    system_prompt = (
        "You are a Planner agent. Your job is to validate user instructions for creating a GitHub item. "
        "Ensure the instruction is actionable and within reasonable scope for a repository task. "
        "Determine if it should indeed be an issue or a PR based on the request."
    )
    
    prompt = f"User Request ({requested_type}): {instruction}\n\nPlease validate this scope."
    
    validation = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=InstructionValidation)
    
    if validation.is_valid:
        print("[Planner] Scope validated.")
        return PlanContext(action=requested_type, context=f"User explicit instruction: {instruction}")
    else:
        print(f"[Planner] Scope validation failed: {validation.reasoning}")
        return None
