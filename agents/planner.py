import json
from pydantic import BaseModel, Field
from typing import Optional
from .llm import get_llm_response
from .message import AgentMessage

class InstructionValidation(BaseModel):
    is_valid: bool = Field(description="Whether the instruction is valid and in scope")
    reasoning: str = Field(description="Reasoning for validation result")
    inferred_action: str = Field(description="Inferred action: 'issue' or 'pr'")

async def plan_route(msg: AgentMessage, session, model: str) -> Optional[AgentMessage]:
    """A2A entrypoint for the Planner."""
    instruction = msg.instruction
    context = msg.context
    
    if instruction == "Decide action from review":
        print("[Planner (A2A)] Interpreting the reviewer's suggested action...")
        suggested = context.get("suggested_action", "").lower()
        
        action = "none"
        if "no action" in suggested or "none" in suggested:
            action = "none"
        elif "issue" in suggested:
            action = "issue"
        elif "pr" in suggested or "pull request" in suggested:
            action = "pr"
            
        if action == "none":
            print("[Planner (A2A)] The previous review concluded that NO ACTION was required. Aborting.")
            return None
            
        out_context = {
            "type": action,
            "review_data": json.dumps(context)
        }
        return AgentMessage(sender="planner", receiver="writer", instruction="Draft new item", context=out_context)
        
    else:
        # Assume it's an explicit instruction from the user 
        requested_type = context.get("type", "issue")
        print(f"[Planner (A2A)] Validating explicit instruction for {requested_type}...")
        
        system_prompt = (
            "You are a Planner agent. Validate user instructions for creating a GitHub item. "
            "Ensure the instruction is actionable and within reasonable scope. "
        )
        prompt = f"User Request ({requested_type}): {instruction}\n\nPlease validate this scope."
        
        validation = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=InstructionValidation)
        
        if validation.is_valid:
            print("[Planner (A2A)] Scope validated.")
            out_context = {
                "type": requested_type,
                "review_data": f"User explicit instruction: {instruction}"
            }
            return AgentMessage(sender="planner", receiver="writer", instruction="Draft new item", context=out_context)
        else:
            print(f"[Planner (A2A)] Scope validation failed: {validation.reasoning}")
            return None
