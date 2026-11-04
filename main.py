"""IT Access & Compliance Triage Desk.

  uv run main.py sample_emails   -> answer every email in that folder once, then offer the report
  uv run main.py                 -> asks you for the folder name
  uv run main.py eval            -> evaluate the RAG systems with LangSmith
"""
import sys
from pathlib import Path

from app.pipeline import email_graph, TICKETS
from app.report import make_report


def read_email(path):
    """Email file format (line by line):
        From: divya.pillai@acme.com
        Subject: Read access to prod-db
        (blank line)
        body ...
    Returns None when the file is not an email."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()   # utf-8-sig also reads Notepad files
    if len(lines) < 3 or not lines[0].startswith("From:"):
        return None
    return {
        "email_id": path.stem,
        "sender": lines[0].removeprefix("From:").strip(),
        "subject": lines[1].removeprefix("Subject:").strip(),
        "body": "\n".join(lines[3:]).strip(),
    }


def run_one_email(email):
    """Run the LangGraph workflow for one email and print the reply."""
    print("=" * 70)
    print(f"NEW EMAIL {email['email_id']} from {email['sender']}: {email['subject']}")
    print("=" * 70)
    state = email_graph.invoke(email)
    print("\nREPLY EMAIL:")
    print(f"To: {email['sender']}")
    print(f"Subject: Re: {email['subject']}\n")
    print(state["reply"])
    print()


def process_folder(folder_name):
    folder = Path(folder_name)
    if not folder.is_dir():
        print(f"Folder not found: {folder}")
        return

    print("LangGraph email workflow:")
    print(email_graph.get_graph().draw_ascii())

    for path in sorted(folder.glob("*.txt")):
        email = read_email(path)
        if email is None:
            print(f"Skipped {path.name}: not an email (it must start with 'From:')")
            continue
        run_one_email(email)

    print(f"Answered {len(TICKETS)} email(s).")
    if len(TICKETS) == 0:
        return
    if input("Make end-of-day report now? (y/n): ").strip().lower() == "y":
        make_report()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    else:
        arg = input("Enter the mail folder name [sample_emails]: ").strip() or "sample_emails"

    if arg == "eval":
        from app.evals import run_evals   # imported only here: it builds the FAISS index (costs an API call)
        run_evals()
    else:
        process_folder(arg)
