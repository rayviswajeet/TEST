"""LangGraph: the email workflow as a StateGraph."""
import json
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from app.guardrails import BLOCKED_MSG
from app.desk import extractor, handle_request
from app.gateway import draft_reply

TICKETS = []   # every email answered in this run (report.py reads this list)


# 1. Shared memory (state) passed between the nodes
class EmailState(TypedDict, total=False):
    email_id: str
    sender: str
    subject: str
    body: str
    ticket: dict | None
    answer: str
    reply: str


# 2. Node 1: security checks + read the email into a Ticket
def extract_node(state: EmailState):
    """Run guardrails and turn the email into a Ticket (None if blocked)."""
    print("[LangGraph] node 'extract'")
    result = extractor.invoke({"messages": [HumanMessage(content=state["body"])]})
    ticket = result.get("structured_response")
    if ticket is None:
        print("[Guardrails] prompt injection BLOCKED")
        return {"ticket": None, "answer": BLOCKED_MSG}
    print(f"[Structured Output] {ticket.model_dump()}")
    return {"ticket": ticket.model_dump()}


# 3. Router: pick the next node
def route_after_extract(state: EmailState):
    """Blocked emails skip the desk and go straight to reply."""
    if state["ticket"] is None:
        return "reply"
    return "desk"


# 4. Node 2: handle the IT request
def desk_node(state: EmailState):
    """Desk agent: tools + policy search + human approval."""
    print("[LangGraph] node 'desk' - ReAct loop: model -> tools -> model ... (create_agent)")
    prompt = f"Ticket: {json.dumps(state['ticket'])}\n\nOriginal email:\n{state['body']}"
    answer = handle_request(prompt, customer=state["sender"])
    return {"answer": answer}


# 5. Node 3: write the reply + remember the ticket for the report
def reply_node(state: EmailState):
    """Write the reply email and add the ticket to TICKETS."""
    print("[LangGraph] node 'reply'")
    if state["ticket"] is None:
        body = (
            "Hello,\n\nYour message could not be processed because it breaks our IT request rules. "
            "Please send a normal access or support request.\n\nRegards,\nIT Access Desk"
        )
    else:
        body = draft_reply(state["ticket"], state["answer"])

    TICKETS.append({
        "email_id": state["email_id"],
        "from": state["sender"],
        "ticket": state["ticket"],
        "answer": state["answer"],
    })
    return {"reply": body}


# 6. Wire the graph together
builder = StateGraph(EmailState)
builder.add_node("extract", extract_node)
builder.add_node("desk", desk_node)
builder.add_node("reply", reply_node)

builder.add_edge(START, "extract")
builder.add_conditional_edges("extract", route_after_extract, ["desk", "reply"])
builder.add_edge("desk", "reply")
builder.add_edge("reply", END)

email_graph = builder.compile()
