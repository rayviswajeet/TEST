# IT Access & Compliance Triage Desk

An employee sends an email. The AI agent reads it, checks the employee, the server and the
company policy, asks a manager to approve if access is needed, and sends a reply email.

Built only with the topics from Krish Naik's
"Complete Agentic AI Course In 10 Hours".

## The full flow

```
 Employee                     AI Triage Desk (main.py)                          Manager
 --------                     ------------------------                          -------
 mail folder    ────────────► 1. extract  (Guardrails + Structured output)
                                    │  blocked? ──────────────────────┐
                                    ▼                                 │
                               2. desk agent (Tools + Vectorless RAG) │
                                    │  wants to grant access?         │
                                    ├────── approve / edit / reject ◄─┼──── types in terminal
                                    ▼                                 │
                               3. reply (LLM Gateway writes email) ◄──┘
 terminal ◄─────────────────────────┘
                               (whole flow = LangGraph StateGraph)

 End of run:  "Make end-of-day report now? (y/n)"  ──► Deep Agent ──► report printed in the terminal
 Quality:     uv run main.py eval    ──► LangSmith evaluates Vector RAG vs Vectorless RAG
```

## Where each video topic is used

| Video topic | File | What it does in the flow |
|-------------|------|--------------------------|
| LangChain (structured output) | `app/desk.py` | Turns the email into a `Ticket` |
| Guardrails (PII + custom middleware) | `app/guardrails.py` | Hides email/phone/card, blocks prompt injection |
| Tools | `app/tools.py` | Look up employee, check server, grant access |
| Vectorless RAG | `app/rag.py` | `search_policy` tool used by the desk agent |
| Vector RAG (FAISS) | `app/rag.py` | Compared with vectorless RAG in the evaluation |
| Human-in-the-Loop | `app/desk.py` | Pauses before every grant for manager approval |
| LangGraph | `app/pipeline.py` | The email workflow: extract → desk → reply |
| LLM Gateway (LiteLLM) | `app/gateway.py` | Writes the reply email: routing, fallback, cache, cost |
| Deep Agents | `app/report.py` | End-of-day compliance report with a sub-agent |
| LLM Evaluation (LangSmith) | `app/evals.py` | Scores both RAG systems on a golden dataset |

The notebook `access_triage_desk_simple.ipynb` explains every topic step by step.

## Setup (uv, same steps as the video)

```powershell
uv init
uv venv
.venv\Scripts\activate
uv add -r requirements.txt
copy .env.example .env
```

Open `.env` and add your keys (`OPENAI_API_KEY` is required; `GROQ_API_KEY` is the backup model;
`LANGSMITH_API_KEY` is needed for `eval`). `uv init` keeps the existing `main.py`.

## Run the full flow

Give the folder that contains the emails:
```powershell
uv run main.py sample_emails
```
Or just run `uv run main.py` and type the folder name when it asks.

### What you will see
Everything is printed in the terminal. Nothing is saved to files.

1. **The LangGraph graph** of the email workflow (drawn in the terminal).
2. **For every email, one labelled line per topic**, for example:
```
[LangGraph] node 'extract'
[Structured Output] {'requester': 'Divya Pillai', 'request_type': 'access_request', 'system': 'prod-db', ...}
[LangGraph] node 'desk' - ReAct loop: model -> tools -> model ... (create_agent)
[Memory] thread_id=divya.pillai@acme.com | messages remembered from earlier emails: 0
[Tools] check_ad_groups(EMP-2002) -> Divya Pillai, active, employee, MFA=True
[Tools] search_policy(max read access hours on prod-db)
[Vectorless RAG] LLM picked sections: ['1.3 Read Access']
[Human-in-the-Loop] agent PAUSED before grant_system_access - waiting for the approver
   approve / edit / reject: approve
[Tools] grant_system_access(EMP-2002, prod-db, read, 48h) -> Granted ...
[LangGraph] node 'reply'
[LLM Gateway] route=smart -> model=gpt-4o | time=1.2s | tokens=310 | cost=$0.001200
```
3. **The reply email** for each email.
4. At the end: **"Make end-of-day report now? (y/n)"** - the Deep Agent prints the compliance report.

Each run answers every email in the folder once, then stops. Run it again to answer them again.

**Evaluation:**
```powershell
uv run main.py eval      # -> scores in the terminal + experiments in LangSmith
```

## How data moves between files

Only two patterns are used:
1. **Normal case:** pass it as a function argument and `return` the result (LangGraph state does this between nodes).
2. **A `@tool` the LLM calls needs it:** a list at the top of one file, `.append()` where it is written,
   `from app.x import LIST` where it is read. Example: `TICKETS` in `app/pipeline.py`, `GRANTS` in `app/tools.py`,
   both read by `app/report.py`.

## Folders and files

| Path | Purpose |
|------|---------|
| `sample_emails/` | Example emails (use it as the mail folder, or make your own folder) |
| `employees.json` | Employee directory |
| `it_security_policy.md` | Company policy used by RAG |
| `incoming_requests.json` | Same sample emails, used by the notebook |

Email file format:
```
From: divya.pillai@acme.com
Subject: Read access to prod-db

Hi team, I need read access to prod-db for 48 hours to debug INC-4412.
```
