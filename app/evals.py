"""Topic: LLM Evaluation - LangSmith scores both RAG systems on the same questions."""
from pydantic import BaseModel
from langsmith import Client, evaluate
from app.config import llm
from app.rag import build_vector_store, vector_rag, vectorless_rag

DATASET = "it-policy-qa"
EXAMPLES = [
    ("What is the minimum password length?", "14 characters"),
    ("How long may a just-in-time privileged session last?", "At most 8 hours"),
    ("How often are privileged accounts re-certified?", "Monthly"),
    ("Can a contractor get admin access to aws-prod?", "No, contractors may never hold write or admin access to Restricted systems"),
]

vector_store = build_vector_store()   # built once (this file is only loaded by: uv run main.py eval)


# 1. The two systems we test: question in -> answer out
def ask_vector_rag(inputs):
    return {"answer": vector_rag(inputs["question"], vector_store)}


def ask_vectorless_rag(inputs):
    return {"answer": vectorless_rag(inputs["question"])}


# 2. The judge: an LLM says if the answer means the same as the reference answer
class Grade(BaseModel):
    correct: bool


def correctness(inputs, outputs, reference_outputs):
    prompt = f"""Question: {inputs['question']}
Reference answer: {reference_outputs['answer']}
Student answer: {outputs['answer']}
Is the student answer correct?"""
    grade = llm.with_structured_output(Grade).invoke(prompt)
    return grade.correct


# 3. Upload the questions (first time only), then score both systems
def run_evals():
    client = Client()
    if not client.has_dataset(dataset_name=DATASET):
        client.create_dataset(dataset_name=DATASET)
        for question, answer in EXAMPLES:
            client.create_example(dataset_name=DATASET, inputs={"question": question}, outputs={"answer": answer})
    print(f"[LLM Evaluation] dataset: {DATASET} ({len(EXAMPLES)} questions)")

    for name, system in [("vector-rag", ask_vector_rag), ("vectorless-rag", ask_vectorless_rag)]:
        results = evaluate(system, data=DATASET, evaluators=[correctness], experiment_prefix=name)
        score = results.to_pandas()["feedback.correctness"].mean()
        print(f"[LLM Evaluation] {name} correctness = {round(score * 100)}%")
    print("Open smith.langchain.com to compare the two experiments.")
