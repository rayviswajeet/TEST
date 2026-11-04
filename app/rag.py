"""Topic: RAG - answer questions from the IT security policy.

1. Split the policy into sections (one per heading).
2. Vector RAG     : FAISS finds the sections closest to the question  (used by evals.py)
3. Vectorless RAG : the LLM reads a table of contents and picks sections (used by the desk agent)
4. search_policy  : the tool the desk agent calls
"""
from pydantic import BaseModel
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import MarkdownHeaderTextSplitter
from app.config import llm, POLICY_FILE

# 1. Split the policy at its "##" and "###" headings
with open(POLICY_FILE, encoding="utf-8") as f:
    policy = f.read()

splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "chapter"), ("###", "section")])
sections = splitter.split_text(policy)


def answer_from(context, question):
    prompt = f"""Answer ONLY from this context. If the answer is not there, say "I don't know".

{context}

Question: {question}"""
    return llm.invoke(prompt).content


# 2. Vector RAG
def build_vector_store():
    return FAISS.from_documents(sections, OpenAIEmbeddings(model="text-embedding-3-small"))


def vector_rag(question, vector_store):
    docs = vector_store.similarity_search(question, k=3)
    context = ""
    for doc in docs:
        print(f"[Vector RAG] FAISS found: {doc.metadata}")
        context += f"{doc.metadata}\n{doc.page_content}\n\n"
    return answer_from(context, question)


# 3. Vectorless RAG
table_of_contents = ""
for number, section in enumerate(sections):
    table_of_contents += f"{number}: {section.metadata}\n"


class SectionPick(BaseModel):
    section_numbers: list[int]


def vectorless_rag(question):
    print(f"[Vectorless RAG] Q: {question}")
    prompt = f"""Question: {question}

Table of contents:
{table_of_contents}
Which section numbers answer the question?"""
    pick = llm.with_structured_output(SectionPick).invoke(prompt)

    context = ""
    for number in pick.section_numbers:
        if 0 <= number < len(sections):
            print(f"[Vectorless RAG] LLM picked section {number}: {sections[number].metadata}")
            context += f"{sections[number].metadata}\n{sections[number].page_content}\n\n"
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
