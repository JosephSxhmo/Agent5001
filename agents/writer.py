from pydantic import BaseModel, Field
from typing import List, Optional
from .llm import get_llm_response

class IssueDraft(BaseModel):
    title: str = Field(description="Title of the Issue")
    problem_description: str = Field(description="Detailed problem description")
    evidence: str = Field(description="Evidence or context supporting the issue")
    acceptance_criteria: List[str] = Field(description="List of acceptance criteria")
    risk_level: str = Field(description="Risk level (low, medium, high)")
    
    def format_body(self) -> str:
        ac = "\n".join(f"- [ ] {item}" for item in self.acceptance_criteria)
        return (
            f"## Problem Description\n{self.problem_description}\n\n"
            f"## Evidence\n{self.evidence}\n\n"
            f"## Acceptance Criteria\n{ac}\n\n"
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
        files = "\n".join(f"- `{f}`" for f in self.files_affected)
        tests = "\n".join(f"- {t}" for t in self.test_plan)
        return (
            f"## Summary\n{self.summary}\n\n"
            f"## Files Affected\n{files}\n\n"
            f"## Behavior Change\n{self.behavior_change}\n\n"
            f"## Test Plan\n{tests}\n\n"
            f"**Risk Level:** {self.risk_level.capitalize()}"
        )

def draft_issue(context: str, model: str = "gpt-4o") -> IssueDraft:
    """Drafts a new GitHub Issue based on context."""
    print("[Writer] Drafting Issue...")
    
    system_prompt = (
        "You are an expert Writer agent. Your task is to draft a structured GitHub Issue based on the provided context. "
        "You must ensure the output strictly adheres to the IssueDraft schema."
    )
    
    prompt = f"Context:\n{context}\n\nPlease draft the Issue."
    return get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=IssueDraft)

def draft_pr(context: str, model: str = "gpt-4o") -> PRDraft:
    """Drafts a new GitHub Pull Request based on context."""
    print("[Writer] Drafting Pull Request...")

    system_prompt = (
        "You are an expert Writer agent. Your task is to draft a structured GitHub Pull Request based on the provided context. "
        "You must ensure the output strictly adheres to the PRDraft schema."
    )
    
    prompt = f"Context:\n{context}\n\nPlease draft the PR."
    return get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=PRDraft)

def improve_draft(original_title: str, original_body: str, critique: str, item_type: str, model: str = "gpt-4o") -> any:
    """Improves an existing draft based on a critique."""
    print(f"[Writer] Improving existing {item_type} based on critique...")
    
    system_prompt = (
        f"You are an expert Writer agent. Your task is to rewrite an existing GitHub {item_type} based on critique. "
        "Address vague language, missing information, and formulate a structured, professional version."
    )
    
    prompt = (
        f"Original Title: {original_title}\n\n"
        f"Original Body:\n{original_body}\n\n"
        f"Critique:\n{critique}\n\n"
        f"Please provide an improved structured version."
    )
    
    if item_type.lower() == "issue":
        return get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=IssueDraft)
    else:
        return get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=PRDraft)
