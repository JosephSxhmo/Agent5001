import argparse
import sys
import os
#Testing The PR Bot
from agents.reviewer import review_code_changes, critique_existing_item
from agents.planner import plan_from_review, plan_from_instruction, load_plan, save_plan, clear_plan
from agents.writer import draft_issue, draft_pr, improve_draft
from agents.gatekeeper import reflect_on_draft, save_pending_draft, load_pending_draft, gatekeeper_approve, PendingDraft, clear_pending_draft
from tools.git import get_git_diff, get_current_branch
from tools.github import get_issue, create_issue, create_pull_request

def main():
    parser = argparse.ArgumentParser(description="Personalized GitHub Repository Agent")
    
    # Global model argument
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model to use (e.g., gpt-4o, ollama/llama3)")
    
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # review command
    review_parser = subparsers.add_parser("review", help="Review local code changes")
    review_parser.add_argument("--base", help="Base branch/commit to compare against", default=None)
    review_parser.add_argument("--range", help="Commit range (e.g. HEAD~3..HEAD)", default=None)
    
    # draft command
    draft_parser = subparsers.add_parser("draft", help="Draft an Issue or PR")
    draft_parser.add_argument("type", choices=["issue", "pr"], help="Type to draft")
    draft_parser.add_argument("--instruction", help="Explicit instruction", default=None)
    
    # approve command
    approve_parser = subparsers.add_parser("approve", help="Approve or reject a pending draft")
    approve_parser.add_argument("--yes", action="store_true", help="Approve draft")
    approve_parser.add_argument("--no", action="store_true", help="Reject draft")
    
    # improve command
    improve_parser = subparsers.add_parser("improve", help="Improve an existing Issue or PR")
    improve_parser.add_argument("type", choices=["issue", "pr"], help="Type to improve")
    improve_parser.add_argument("--number", type=int, required=True, help="GitHub Issue/PR Number")
    
    args = parser.parse_args()
    
    # Needs repository name and owner
    owner = "JosephSxhmo"
    repo = "Agent5001"
    
    if args.command == "review":
        try:
            diff = get_git_diff(args.base, args.range)
        except Exception as e:
            print("[Error] Failed to get git diff. Are you in a git repository with the specified branch?")
            sys.exit(1)
            
        if not diff:
            print("[Tool] No diff found.")
            sys.exit(0)
            
        review_res = review_code_changes(diff, model=args.model)
        print("\n--- Review Summary ---")
        print(review_res.summary)
        print(f"Suggested Action: {review_res.suggested_action}")
        print("----------------------\n")
        
        plan = plan_from_review(review_res)
        save_plan(plan)
        print("[Planner] Saved plan context. Run `agent draft issue` or `agent draft pr` to proceed.")
        
    elif args.command == "draft":
        # Get context
        plan = None
        if args.instruction:
            plan = plan_from_instruction(args.instruction, args.type, model=args.model)
        else:
            plan = load_plan()
            if not plan:
                print("[Error] No active plan found and no --instruction provided.")
                sys.exit(1)
            if plan.action != args.type and plan.action != "none":
                 print(f"[Warning] Resuming saved plan. Plan suggested action '{plan.action}' but crafting '{args.type}'.")
        
        if not plan:
            sys.exit(1)
            
        if plan.action == "none" and not args.instruction:
            print("[Warning] The previous review concluded that NO ACTION was required. Aborting draft.")
            sys.exit(0)
            
        # Draft content
        draft_content = None
        if args.type == "issue":
            draft_content = draft_issue(plan.context, model=args.model)
        else:
            draft_content = draft_pr(plan.context, model=args.model)
            
        # Gatekeeper reflection
        verdict = reflect_on_draft(draft_content, args.type, model=args.model)
        
        print("\n--- DRAFT ---")
        print(f"Title: {draft_content.title}")
        print("Body:")
        formatted_body = draft_content.format_body()
        print(formatted_body)
        print("-------------\n")
        
        if verdict.pass_validation:
            print("[Gatekeeper] Reflection verdict: PASS")
            # Save for approval
            pending = PendingDraft(item_type=args.type, title=draft_content.title, body=formatted_body)
            save_pending_draft(pending)
            print("Action required: Run `agent approve --yes` or `agent approve --no`")
        else:
            print("[Gatekeeper] Reflection verdict: FAIL")
            print("Revision required before saving draft.")
            
    elif args.command == "approve":
        pending = load_pending_draft()
        if not pending:
            print("[Error] No pending drafts to approve.")
            sys.exit(1)
            
        if args.yes:
            if gatekeeper_approve(True):
                if pending.item_type == "issue":
                    create_issue(owner, repo, pending.title, pending.body)
                else:
                    head_branch = get_current_branch()
                    if not head_branch or head_branch == "HEAD":
                        print("[Error] Cannot create PR from a detached HEAD or empty branch. Please checkout a named branch.")
                        sys.exit(1)
                    
                    base_branch = "main"
                    # In a real workflow, you would push the branch first, but this tests the API call.
                    create_pull_request(owner, repo, pending.title, pending.body, head_branch, base_branch)
                print("[Tool] GitHub API call completed.")
                clear_pending_draft()
                clear_plan()
        elif args.no:
            gatekeeper_approve(False)
        else:
            print("Please specify --yes or --no")
            
    elif args.command == "improve":
        github_item = get_issue(owner, repo, args.number)
        if not github_item:
            sys.exit(1)
            
        original_title = github_item.get("title", "")
        original_body = github_item.get("body", "")
        
        critique_res = critique_existing_item(original_title, original_body, args.type, model=args.model)
        
        print("\n--- Critique ---")
        for mi in critique_res.missing_info:
            print(f"- Missing: {mi}")
        print("----------------\n")
        
        improved_draft = improve_draft(original_title, original_body, critique_res.critique_summary, args.type, model=args.model)
        
        verdict = reflect_on_draft(improved_draft, args.type, model=args.model)
        
        print("\n--- IMPROVED DRAFT ---")
        print(f"Title: {improved_draft.title}")
        formatted = improved_draft.format_body()
        print(formatted)
        print("----------------------\n")
        
        if verdict.pass_validation:
            print("[Gatekeeper] Reflection verdict: PASS")
            pending = PendingDraft(item_type=args.type, title=improved_draft.title, body=formatted)
            save_pending_draft(pending)
            print("Action required: Run `agent approve --yes` or `agent approve --no`")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
