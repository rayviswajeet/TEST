"""Topic: LLM Evaluation - LangSmith tests both RAG systems on the same questions.

1. Questions + correct answers  (the dataset)
2. The two systems we test      (question in -> answer out)
3. The judge                    (an LLM says if the answer is correct)
4. run_evals                    (upload the dataset once, then evaluate each system)
"""
from langsmith import Client, evaluate
from app.config import llm
from app.rag import build_vector_store, vector_rag, vectorless_rag

# 1. The dataset
DATASET = "it-policy-qa-v2"   # new name: an existing dataset is never re-uploaded
EXAMPLES = [
    {"inputs": {"question": "What is the minimum password length?"},
     "reference_outputs": {"answer": "14 characters"}},
    {"inputs": {"question": "What does a person need before getting write or admin access?"},
     "reference_outputs": {"answer": "They must be enrolled in MFA (and on a Restricted system also need an open incident ticket)"}},
    {"inputs": {"question": "How often are privileged accounts re-certified?"},
     "reference_outputs": {"answer": "Monthly"}},
    {"inputs": {"question": "Can a contractor get admin access to aws-prod?"},
     "reference_outputs": {"answer": "No, contractors may never hold write or admin access to Restricted systems"}},
]


# 2. The two systems we test
vector_store = build_vector_store()   # built once (this file is only loaded by: uv run main.py eval)


def ask_vector_rag(inputs):
    return {"answer": vector_rag(inputs["question"], vector_store)}


def ask_vectorless_rag(inputs):
    return {"answer": vectorless_rag(inputs["question"])}


# 3. The judge
def correctness(inputs, outputs, reference_outputs):
    prompt = f"""Question: {inputs['question']}
Correct answer: {reference_outputs['answer']}
Student answer: {outputs['answer']}
Does the student answer mean the same as the correct answer? Reply with only yes or no."""
    reply = llm.invoke(prompt).content
    is_correct = reply.strip().lower().startswith("yes")
    print(f"[LLM Evaluation] correct: {is_correct}\n")
    return is_correct


# 4. Upload the dataset (first time only), then evaluate both systems
def run_evals():
    client = Client()
    if not client.has_dataset(dataset_name=DATASET):
        client.create_dataset(dataset_name=DATASET)
        client.create_examples(dataset_name=DATASET, examples=EXAMPLES)

    print("[LLM Evaluation] ===== Vector RAG (FAISS) =====")
    evaluate(ask_vector_rag, data=DATASET, evaluators=[correctness], experiment_prefix="vector-rag")

    print("[LLM Evaluation] ===== Vectorless RAG =====")
    evaluate(ask_vectorless_rag, data=DATASET, evaluators=[correctness], experiment_prefix="vectorless-rag")

    print("Open smith.langchain.com to compare the two experiments side by side.")
