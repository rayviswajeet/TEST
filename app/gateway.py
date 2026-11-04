"""Topic: LLM Gateway (LiteLLM) - one Router in front of several models.

Routing  : "fast" and "smart" are nicknames for real models.
Fallback : if OpenAI fails, the Groq "backup" model answers.
Cache    : the same prompt twice is answered from memory.
Cost     : LiteLLM tells us what each call cost.
"""
import litellm
from litellm import Router
from litellm.caching import Cache

litellm.suppress_debug_info = True
litellm.cache = Cache(type="local")

# 1. The router: nickname -> real model
router = Router(
    model_list=[
        {"model_name": "fast",   "litellm_params": {"model": "gpt-4o-mini"}},
        {"model_name": "smart",  "litellm_params": {"model": "gpt-4o"}},
        {"model_name": "backup", "litellm_params": {"model": "groq/llama-3.3-70b-versatile"}},
    ],
    fallbacks=[{"fast": ["backup"]}, {"smart": ["backup"]}],
)


# 2. Write the reply email
def draft_reply(ticket, desk_answer):
    if ticket["request_type"] == "access_request":
        model = "smart"      # access requests matter more -> better model
    else:
        model = "fast"

    prompt = f"""Write a short, polite email reply to an employee from the IT Access Desk.
Use ONLY the facts in the desk answer. Do not promise anything else.
Start with "Hi <first name>," and end with "Regards," and "IT Access Desk" on the next line.

Employee: {ticket['requester']}
Their request: {ticket['summary']}
Desk answer: {desk_answer}"""

    response = router.completion(model=model, messages=[{"role": "user", "content": prompt}], caching=True)

    try:
        cost = litellm.completion_cost(completion_response=response)
    except Exception:
        cost = 0     # price unknown (e.g. the Groq backup model)
    print(f"[LLM Gateway] {model} -> {response.model} | tokens={response.usage.total_tokens} | cost=${round(cost, 6)}")

    return response.choices[0].message.content
