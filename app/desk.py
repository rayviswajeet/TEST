"""Topics: Structured output + Human-in-the-Loop.

1. extractor : reads an email and fills in a Ticket.
2. desk      : agent with tools that decides the request; pauses before granting access.
3. ask_human : the manager types approve / edit / reject in the terminal.
4. handle_request : runs the desk and resumes it after each human answer.
"""
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.config import llm
from app.guardrails import GUARDRAILS
from app.tools import check_ad_groups, ping_server_status, grant_system_access
from app.rag import search_policy


# 1. Structured output: the LLM must answer with exactly these fields
class Ticket(BaseModel):
    requester: str = Field(description="Full name of the person who wrote the email")
    request_type: str = Field(description="One of: access_request, it_support, other")
    system: str = Field(description="One of: prod-db, aws-prod, vpn, jira, none")
    access_level: str = Field(description="One of: read, write, admin, none")
    duration_hours: int = Field(description="Requested hours, 0 if not given")
    urgency: str = Field(description="One of: low, medium, high, critical")
    summary: str = Field(description="One-sentence summary of the request")


extractor = create_agent(
    llm,
    tools=[],
    system_prompt="Extract the ticket details from the employee's email.",
    response_format=Ticket,
    middleware=GUARDRAILS,
)


# 2. The desk agent
DESK_PROMPT = """You are the IT Access Desk. You decide access requests yourself.
A human manager checks every grant automatically when you call grant_system_access.

Access requests - follow these steps:
1. check_ad_groups: the employee must be active.
2. ping_server_status for the system.
3. search_policy with a specific question, e.g. "What is the maximum read access duration for prod-db?"
4. If the policy allows it, CALL grant_system_access (employee_id, system, access_level, hours,
   and the incident ticket as reason). If the hours are too long, use the maximum the policy allows.
5. Refuse only when a policy rule clearly forbids it, and name that rule.
Never tell the employee to ask their manager - calling grant_system_access IS the approval step.

IT support problems (no access needed): check the server status and give clear next steps.
Finish with a short answer for the employee."""

desk = create_agent(
    llm,
    tools=[check_ad_groups, ping_server_status, search_policy, grant_system_access],
    system_prompt=DESK_PROMPT,
    middleware=GUARDRAILS + [HumanInTheLoopMiddleware(interrupt_on={"grant_system_access": True})],
    checkpointer=MemorySaver(),   # remembers each sender's earlier emails (thread_id = sender)
)


# 3. Human-in-the-Loop: ask the manager in the terminal
def ask_human(args):
    print(f"\n[Human-in-the-Loop] agent PAUSED. It wants to call grant_system_access with: {args}")
    answer = input("   approve / edit / reject: ").strip().lower()
    while answer not in ["approve", "edit", "reject"]:      # a typo must never grant access
        answer = input("   Please type approve, edit or reject: ").strip().lower()

    if answer == "approve":
        return {"type": "approve"}

    if answer == "reject":
        reason = input("   Reason: ")
        return {"type": "reject", "message": reason}

    # answer == "edit": change the hours, keep everything else
    hours = input("   New duration in hours: ").strip()
    while not hours.isdigit():
        hours = input("   Please type a whole number: ").strip()
    args["duration_hours"] = int(hours)
    return {"type": "edit", "edited_action": {"name": "grant_system_access", "args": args}}


# 4. Run the desk; every time it pauses, ask the human and resume
def handle_request(text, customer):
    config = {"configurable": {"thread_id": customer}}
    result = desk.invoke({"messages": [{"role": "user", "content": text}]}, config)

    while "__interrupt__" in result:
        decisions = []
        for request in result["__interrupt__"][0].value["action_requests"]:
            decisions.append(ask_human(request["args"]))
        result = desk.invoke(Command(resume={"decisions": decisions}), config)

    return result["messages"][-1].content
