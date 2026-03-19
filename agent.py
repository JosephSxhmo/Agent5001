import argparse
import sys
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
#Testing the Reviewer, action must be taken for this comment
from agents.message import AgentMessage
from agents.planner import plan_route
from agents.reviewer import review_route
from agents.writer import writer_route
from agents.gatekeeper import gatekeeper_route, gatekeeper_approve

async def a2a_orchestrator(args):
    """The central message bus routing messages between agents and hosting the MCP client."""
    server_params = StdioServerParameters(
        command="venv/bin/python3",
        args=["tools/mcp_server.py"]
    )
    
    print("[System] Connecting to MCP Server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("[System] MCP Client Initialized.")
            
            # Message Queue
            messages = []
            
            # Initial User Prompt injection to the bus
            if args.command == "review":
                messages.append(AgentMessage(sender="user", receiver="reviewer", instruction="Review local code changes"))
            elif args.command == "draft":
                instruction = args.instruction or f"Draft a new {args.type} based on current state."
                messages.append(AgentMessage(sender="user", receiver="planner", instruction=instruction, context={"type": args.type}))
            elif args.command == "improve":
                messages.append(AgentMessage(sender="user", receiver="reviewer", instruction="Critique existing item", context={"type": args.type, "number": args.number}))
            elif args.command == "approve":
                # Special bypass just for approval processing via Gatekeeper
                await gatekeeper_approve(args.yes, session)
                return

            # Main A2A Event Loop
            max_iterations = 15
            iters = 0
            while messages and iters < max_iterations:
                msg = messages.pop(0)
                print(f"\n[A2A Bus] Routing message from '{msg.sender}' to '{msg.receiver}'")
                
                if msg.receiver == "planner":
                    next_msg = await plan_route(msg, session, args.model)
                    if next_msg: messages.append(next_msg)
                elif msg.receiver == "reviewer":
                    next_msg = await review_route(msg, session, args.model)
                    if next_msg: messages.append(next_msg)
                elif msg.receiver == "writer":
                    next_msg = await writer_route(msg, session, args.model)
                    if next_msg: messages.append(next_msg)
                elif msg.receiver == "gatekeeper":
                    next_msg = await gatekeeper_route(msg, session, args.model)
                    if next_msg: messages.append(next_msg)
                
                iters += 1
                
            if iters >= max_iterations:
                print("[System] Hit maximum A2A loop iterations. Terminating.")

def main():
    parser = argparse.ArgumentParser(description="A2A + MCP Personalized GitHub Agent")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model to use (e.g., gpt-4o, ollama/llama3)")
    
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # review command
    review_parser = subparsers.add_parser("review", help="Review local code changes")
    
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
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # Execute the async core loop
    asyncio.run(a2a_orchestrator(args))

if __name__ == "__main__":
    main()
