import json
import sys
from pathlib import Path

# Make the project root importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag_chain import ask_financial_rag


QUESTIONS_FILE = PROJECT_ROOT / "evaluation" / "questions.json"


def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Handle either:
    # 1. A simple list of question objects
    # 2. A dictionary containing question lists by category
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        questions = []

        for category, items in data.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        questions.append(item)

        return questions

    raise ValueError("Unsupported questions.json format.")


def main():
    questions = load_questions()

    print("=" * 80)
    print("FINANCIAL RAG - 25 QUESTION EVALUATION")
    print("=" * 80)

    print(f"Loaded questions: {len(questions)}")

    completed = 0
    failed = 0

    for index, item in enumerate(questions, start=1):
        question_id = item.get("id", f"Q{index}")
        question = item.get("question", "")

        print("\n" + "-" * 80)
        print(f"{index}. {question_id}")
        print(f"QUESTION: {question}")

        try:
            result = ask_financial_rag(question)

            answer = result.get("answer", "")
            route = result.get("route", "unknown")

            print(f"ROUTE: {route}")
            print(f"ANSWER: {answer}")
            print("STATUS: COMPLETED")

            completed += 1

        except Exception as error:
            print(f"ERROR: {error}")
            print("STATUS: FAILED")
            failed += 1

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print(f"Questions completed: {completed}")
    print(f"Questions failed:    {failed}")
    print(f"Total questions:     {len(questions)}")
    print("=" * 80)


if __name__ == "__main__":
    main()