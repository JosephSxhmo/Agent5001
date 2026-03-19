import json
from pydantic import BaseModel, Field
from typing import List, Optional
from .llm import get_llm_response
from .message import AgentMessage

class IssueDraft(BaseModel):
    title: str = Field(description="Title of the Issue")
    problem_description: str = Field(description="Detailed problem description")
    evidence: str = Field(description="Evidence or context supporting the issue")
    acceptance_criteria: List[str] = Field(description="List of acceptance criteria")
    risk_level: str = Field(description="Risk level (low, medium, high)")
    
    def format_body(self) -> str:
        ac = "\\n".join(f"- [ ] {item}" for item in self.acceptance_criteria)
        return (
            f"## Problem Description\\n{self.problem_description}\\n\\n"
            f"## Evidence\\n{self.evidence}\\n\\n"
            f"## Acceptance Criteria\\n{ac}\\n\\n"
            f"**Risk Level:** {self.risk_level.capitalize()}"
        )

class PRDraft(BaseModel):
    title: str = Field(description="Title of the Pull Request")
    summary: str = Field(description="Summary of the changes")
    files_affected: List[str] = Field(description="Files affected by this PR")
    behavior_change: str = Field(description="Description of behavior changes")
    test_plan: List[str] = Field(description="Steps to test the changes")
    risk_level: str = Field(description="Risk level (low, medium, high)")
    
    def format_body(self) -> str:
        files = "\\n".join(f"- `{f}`" for f in self.files_affected)
        tests = "\\n".join(f"- {t}" for t in self.test_plan)
        return (
            f"## Summary\\n{self.summary}\\n\\n"
            f"## Files Affected\\n{files}\\n\\n"
            f"## Behavior Change\\n{self.behavior_change}\\n\\n"
            f"## Test Plan\\n{tests}\\n\\n"
            f"**Risk Level:** {self.risk_level.capitalize()}"
        )

async def writer_route(msg: AgentMessage, session, model: str) -> Optional[AgentMessage]:
    """A2A entrypoint for the Writer."""
    instruction = msg.instruction
    context = msg.context
    
    if instruction == "Draft new item":
        item_type = context.get("type", "issue")
        review_data = context.get("review_data", "")
        
        if item_type == "issue":
            print("[Writer (A2A)] Drafting Issue...")
            system_prompt = (
                "You are an expert Writer agent. Draft a structured GitHub Issue based on the provided JSON context. "
                "You must extract evidence, problem_description, and title directly from the context text."
            )
            prompt = f"Context:\\n{review_data}\\n\\nPlease draft the Issue."
            draft = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=IssueDraft)
        else:
            print("[Writer (A2A)] Drafting Pull Request...")
            system_prompt = (
                "You are an expert Writer agent. Draft a structured GitHub Pull Request based on the provided JSON context. "
                "Extract summary, behavior_change, and files_affected directly from the context text."
            )
            prompt = f"Context:\\n{review_data}\\n\\nPlease draft the PR."
            draft = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=PRDraft)
            
        out_context = {
            "type": item_type,
            "title": draft.title,
            "body": draft.format_body(),
            "raw_draft_json": draft.model_dump_json()
        }
        return AgentMessage(sender="writer", receiver="gatekeeper", instruction="Review generated draft", context=out_context)
        
    elif instruction == "Improve existing draft":
        item_type = context.get("type", "issue")
        original_title = context.get("original_title", "")
        original_body = context.get("original_body", "")
        critique = context.get("critique_summary", "")
        
        print(f"[Writer (A2A)] Improving existing {item_type} based on critique...")
        system_prompt = (
            f"You are an expert Writer agent. Your task is to rewrite an existing GitHub {item_type} based on critique. "
            "Address vague language, missing information, and formulate a structured, professional version."
        )
        prompt = (
            f"Original Title: {original_title}\\n\\n"
            f"Original Body:\\n{original_body}\\n\\n"
            f"Critique:\\n{critique}\\n\\n"
            f"Please provide an improved structured version."
        )
        
        if item_type.lower() == "issue":
            draft = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=IssueDraft)
        else:
            draft = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=PRDraft)
            
        out_context = {
            "type": item_type,
            "title": draft.title,
            "body": draft.format_body(),
            "raw_draft_json": draft.model_dump_json()
        }
        return AgentMessage(sender="writer", receiver="gatekeeper", instruction="Review generated draft", context=out_context)

    return None
