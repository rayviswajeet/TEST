"""Topic: Deep Agents - end-of-day compliance report with a sub-agent."""
import json
from langchain_core.tools import tool
from deepagents import create_deep_agent

from app.config import llm
from app.tools import EMPLOYEES, GRANTS
from app.pipeline import TICKETS


@tool
def get_employee_records() -> str:
    """All employees with status, type, MFA enrollment and AD groups."""
    return json.dumps(EMPLOYEES)


@tool
def get_todays_grants() -> str:
    """All access grants approved in this run."""
    return json.dumps(GRANTS)


@tool
def get_todays_tickets() -> str:
    """All emails processed in this run with their ticket and the desk's answer."""
    return json.dumps(TICKETS)


auditor = {
    "name": "auditor",
    "description": "Checks employees, today's grants and today's tickets for compliance problems.",
    "system_prompt": (
        "Use your tools. Report: leavers or contractors who still have access, today's grants, "
        "anyone without MFA, and a count of today's tickets by type. "
        "Use only names and IDs from the tool output."
    ),
    "tools": [get_employee_records, get_todays_grants, get_todays_tickets],
}

deep_agent = create_deep_agent(
    model=llm,
    system_prompt=(
        "You are the compliance lead. Ask the auditor sub-agent for its findings, then reply with "
        "the full End-of-Day Compliance Report in Markdown as your final message. Do not write files."
    ),
    subagents=[auditor],
)


def make_report():
    print("[Deep Agents] compliance lead is asking the auditor sub-agent ...")
    result = deep_agent.invoke({"messages": [{"role": "user", "content": "Create today's compliance report."}]})
    print(result["messages"][-1].content)
