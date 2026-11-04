"""Topic: RAG - answer questions from the IT security policy.

Vector RAG     : cut the policy into chunks, FAISS finds the chunks closest to the question.
Vectorless RAG : the LLM reads a table of contents and picks the sections itself (PageIndex idea).
"""
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from app.config import llm, POLICY_FILE

# 1. Load the policy and split it at its "##" and "###" headings (one piece per section)
with open(POLICY_FILE, encoding="utf-8") as f:
    policy = f.read()

header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "chapter"), ("###", "section")])
sections = header_splitter.split_text(policy)


def answer_from(context, question):
    """Ask the LLM, allowing it to use only the given context."""
    prompt = f"""Answer ONLY from this context. If the answer is not there, say "I don't know".

{context}

Question: {question}"""
    return llm.invoke(prompt).content


# 2. Vector RAG (FAISS) - used by evals.py
def build_vector_store():
    chunk_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = chunk_splitter.split_documents(sections)
    return FAISS.from_documents(chunks, OpenAIEmbeddings(model="text-embedding-3-small"))


def vector_rag(question, vector_store):
    docs = vector_store.similarity_search(question, k=3)
    print(f"[Vector RAG] FAISS found {len(docs)} chunks for: {question}")
    context = ""
    for doc in docs:
        context += doc.page_content + "\n\n"
    return answer_from(context, question)


# 3. Vectorless RAG - used by the desk agent
table_of_contents = ""
for number, section in enumerate(sections):
    table_of_contents += f"{number}: {section.metadata} - {section.page_content[:100]}\n"


class SectionPick(BaseModel):
    section_numbers: list[int] = Field(description="Numbers of the sections that answer the question")


def vectorless_rag(question):
    print(f"[Vectorless RAG] Q: {question}")
    prompt = f"""Question: {question}

Table of contents:
{table_of_contents}
Which section numbers contain the answer?"""
    pick = llm.with_structured_output(SectionPick).invoke(prompt)

    context = ""
    for number in pick.section_numbers:
        if 0 <= number < len(sections):
            section = sections[number]
            print(f"[Vectorless RAG] LLM picked section {number}: {section.metadata}")
            context += f"{section.metadata}\n{section.page_content}\n\n"   # title too, so the LLM can name the rule
    if context == "":          # the LLM picked nothing -> use the whole (short) policy
        context = policy

    answer = answer_from(context, question)
    print(f"[Vectorless RAG] Answer: {answer}")
    return answer


# 4. The tool the desk agent calls
@tool
def search_policy(question: str) -> str:
    """Search the IT security policy for rules and time limits."""
    print(f"[Tools] search_policy({question})")
    return vectorless_rag(question)
