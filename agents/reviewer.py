from typing import List, Optional
from pydantic import BaseModel, Field
from .llm import get_llm_response

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

def review_code_changes(diff: str, model: str = "gpt-4o") -> ReviewResult:
    """
    Analyzes code changes (diff) and returns a structured ReviewResult.
    """
    system_prompt = (
        "You are an expert Code Reviewer agent. Your task is to analyze the provided git diff, "
        "identify potential issues or improvements, categorize the changes, assess the risk level, "
        "and decide whether to create an Issue, a PR, or take no action. "
        "You must justify your decision using specific evidence from the diff."
    )
    
    prompt = f"Here is the git diff to analyze:\n\n```diff\n{diff}\n```\n\nPlease provide a comprehensive structured review."
    
    print("[Reviewer] Analyzing changes...")
    result = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=ReviewResult)
    return result

class CritiqueResult(BaseModel):
    missing_info: List[str] = Field(description="Unclear or missing information")
    vague_language: List[str] = Field(description="Instances of vague language")
    critique_summary: str = Field(description="Overall critique of the current item")

def critique_existing_item(title: str, body: str, item_type: str, model: str = "gpt-4o") -> CritiqueResult:
    """
    Critiques an existing issue or PR.
    """
    system_prompt = (
        f"You are an expert Reviewer agent. Your task is to critique an existing GitHub {item_type}. "
        "Identify unclear/missing information, detect vague language, and prepare to suggest improvements."
    )
    
    prompt = f"Title: {title}\n\nBody:\n{body}\n\nPlease analyze and critique this {item_type}."
    
    print(f"[Reviewer] Critiquing existing {item_type}...")
    result = get_llm_response(prompt, system_prompt=system_prompt, model=model, response_format=CritiqueResult)
    return result
