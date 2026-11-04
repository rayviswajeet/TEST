"""Topic: Tools - functions the agent can call (3 lookups + 1 high-risk action)."""
import json
from langchain_core.tools import tool
from app.config import EMPLOYEES_FILE

# 1. Data the tools use
with open(EMPLOYEES_FILE, encoding="utf-8") as f:
    EMPLOYEES = json.load(f)          # a list of employee dicts

SERVERS = {
    "prod-db": "Healthy",
    "aws-prod": "Healthy",
    "vpn": "Degraded (Mumbai gateway overloaded, Pune gateway healthy)",
    "jira": "Healthy",
}

GRANTS = []   # every grant approved in this run (report.py reads this list)


def find_employee(name_or_id):
    """Return the employee whose name or ID matches, or None."""
    for emp in EMPLOYEES:
        if name_or_id.lower() in [emp["name"].lower(), emp["employee_id"].lower()]:
            return emp
    return None


# 2. The tools (the docstring tells the LLM what each tool does)
@tool
def check_ad_groups(employee_name_or_id: str) -> dict:
    """Look up an employee's status, type, MFA enrollment, AD groups and manager."""
    emp = find_employee(employee_name_or_id)
    print(f"[Tools] check_ad_groups({employee_name_or_id}) -> {emp}")
    if emp is None:
        return {"error": "Employee not found"}
    return emp


@tool
def ping_server_status(server_name: str) -> str:
    """Check the health of a server: prod-db, aws-prod, vpn or jira."""
    status = SERVERS.get(server_name.lower(), "Unknown server")
    print(f"[Tools] ping_server_status({server_name}) -> {status}")
    return status


@tool
def grant_system_access(employee_id: str, system: str, access_level: str, duration_hours: int, reason: str) -> str:
    """HIGH RISK: give an employee temporary access to a system. Needs human approval."""
    emp = find_employee(employee_id)
    if emp is None:
        print(f"[Tools] grant_system_access({employee_id}) -> employee not found")
        return "Employee not found"

    emp["current_ad_groups"].append(f"{system}-{access_level}")
    grant = {"employee_id": employee_id, "name": emp["name"], "system": system,
             "level": access_level, "hours": duration_hours, "reason": reason}
    GRANTS.append(grant)
    print(f"[Tools] grant_system_access -> {grant}")
    return f"Granted {access_level} on {system} to {emp['name']} for {duration_hours} hours."
