"""Topic: Guardrails - checks that run before the agent sees the email.

1. block_injection : our own check - stop emails that try to override the rules.
2. PIIMiddleware   : built-in - hide emails, card numbers and phone numbers from the model.
"""
from langchain.agents.middleware import before_agent, PIIMiddleware

BLOCKED_MSG = "Blocked: prompt injection detected."
BANNED_PHRASES = ["ignore previous instructions", "ignore all rules", "system prompt", "drop database"]


# 1. Custom guardrail: runs once, before the agent starts
#    (LangChain always passes state and runtime; we only need state)
@before_agent(can_jump_to=["end"])
def block_injection(state, runtime):
    text = state["messages"][-1].content.lower()
    for phrase in BANNED_PHRASES:
        if phrase in text:
            print(f"[Guardrails] blocked, email contains: '{phrase}'")
            return {"messages": [{"role": "assistant", "content": BLOCKED_MSG}], "jump_to": "end"}
    return None   # nothing found -> the agent runs normally


# 2. The list every agent uses (middleware=GUARDRAILS)
GUARDRAILS = [
    block_injection,
    PIIMiddleware("email"),                                   # anna@acme.com       -> [REDACTED_EMAIL]
    PIIMiddleware("credit_card", strategy="mask"),            # 4111 1111 1111 1111 -> ****1111
    PIIMiddleware("phone", detector=r"\+91 \d{5} \d{5}"),     # +91 98200 11002     -> [REDACTED_PHONE]
]
