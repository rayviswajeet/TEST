"""Shared settings: API keys, the LangChain model, and the input files."""
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv(override=True)   # .env values win over old Windows environment variables

EMPLOYEES_FILE = "employees.json"
POLICY_FILE = "it_security_policy.md"

llm = init_chat_model("openai:gpt-4o-mini")   # one LangChain model for every agent
