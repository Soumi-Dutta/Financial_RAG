import os

from dotenv import load_dotenv
from groq import Groq

from src.ingestion import load_data
from src.preprocessing import clean_data
from src.query_router import (
    classify_query,
    split_questions,
    resolve_follow_up_question,
)
from src.query_engine import process_query
from src.retrieval import search
from src.prompts import (
    SYSTEM_PROMPT,
    CALCULATION_PROMPT,
    RETRIEVAL_PROMPT,
)


# =========================================================
# LLM CONFIGURATION
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY was not found. "
        "Please add your Groq API key to the .env file."
    )

client = Groq(
    api_key=GROQ_API_KEY
)

MODEL_NAME = "openai/gpt-oss-20b"


# =========================================================
# HELPERS
# =========================================================

def dataframe_to_text(data):
    """
    Convert a Pandas DataFrame into a readable text table.

    Financial calculations are performed before this function.
    This function only formats the verified result for the LLM.
    """

    if data is None:
        return "No verified calculation result was available."

    if hasattr(data, "to_string"):

        return data.to_string(
            index=False
        )

    return str(data)


# =========================================================
# CALCULATION RESULT FORMATTER
# =========================================================

def format_calculation_result(result):
    """
    Convert a deterministic calculation result into
    structured context for the LLM.
    """

    result_type = result.get(
        "type",
        "",
    )

    calculation = result.get(
        "calculation",
        "",
    )

    source = result.get(
        "source",
        "",
    )

    data = result.get(
        "data"
    )

    table_text = dataframe_to_text(
        data
    )

    return f"""
Calculation type:
{result_type}

Calculation logic:
{calculation}

Source:
{source}

Verified calculation result:
{table_text}
"""


# =========================================================
# SOURCE DETAILS
# =========================================================

def get_calculation_source_details(
    result
):
    """
    Return the calculation evidence that should be
    displayed by the Streamlit source panel.
    """

    return {
        "type": result.get(
            "type",
            "",
        ),
        "source": result.get(
            "source",
            "",
        ),
        "calculation": result.get(
            "calculation",
            "",
        ),
        "verified_data": dataframe_to_text(
            result.get("data")
        ),
    }


def get_retrieval_source_details(
    document
):
    """
    Return structured metadata for a retrieved RAG document.
    """

    return {
        "metadata": document.get(
            "metadata",
            {},
        ),
        "text": document.get(
            "text",
            "",
        ),
        "distance": document.get(
            "distance"
        ),
    }


# =========================================================
# CALCULATION QUESTION
# =========================================================

def answer_calculation_question(
    question,
    data,
):
    """
    Answer a numerical/financial question using the
    deterministic calculation layer.

    Pandas performs the calculation.

    The LLM only converts the verified result into
    a natural-language answer.
    """

    result = process_query(
        question,
        data,
        route="calculation",
    )

    calculation_context = (
        format_calculation_result(
            result
        )
    )

    prompt = CALCULATION_PROMPT.format(
        question=question,
        result=calculation_context,
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    answer = (
        response.choices[0]
        .message
        .content
        .strip()
    )

    return {
        "question": question,
        "answer": answer,
        "route": "calculation",
        "sources": [
            get_calculation_source_details(
                result
            )
        ],
    }


# =========================================================
# RETRIEVAL QUESTION
# =========================================================

def answer_retrieval_question(
    question,
):
    """
    Answer a semantic/document question using the
    FAISS retrieval layer.

    No financial aggregation is performed here.
    """

    documents = search(
        question,
        top_k=5,
    )

    if not documents:

        return {
            "question": question,
            "answer": (
                "I could not find enough relevant "
                "information in the dataset to answer "
                "that question."
            ),
            "route": "retrieval",
            "sources": [],
        }

    evidence_parts = []

    for number, document in enumerate(
        documents,
        start=1,
    ):

        metadata = document.get(
            "metadata",
            {},
        )

        text = document.get(
            "text",
            "",
        )

        evidence_parts.append(
            f"""
Evidence {number}

Metadata:
{metadata}

Text:
{text}
"""
        )

    evidence = "\n".join(
        evidence_parts
    )

    prompt = RETRIEVAL_PROMPT.format(
        question=question,
        context=evidence,
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    answer = (
        response.choices[0]
        .message
        .content
        .strip()
    )

    sources = []

    for document in documents:

        sources.append(
            get_retrieval_source_details(
                document
            )
        )

    return {
        "question": question,
        "answer": answer,
        "route": "retrieval",
        "sources": sources,
    }


# =========================================================
# SINGLE QUESTION
# =========================================================

def answer_single_question(
    question,
    data,
):
    """
    Classify and answer one question.
    """

    route = classify_query(
        question
    )

    if route == "calculation":

        return answer_calculation_question(
            question,
            data,
        )

    return answer_retrieval_question(
        question
    )


# =========================================================
# COMBINE MULTIPLE ANSWERS
# =========================================================

def combine_answers(
    question_results
):
    """
    Combine multiple question answers into one
    readable response.
    """

    if len(question_results) == 1:

        return question_results[0][
            "answer"
        ]

    combined_parts = []

    for number, result in enumerate(
        question_results,
        start=1,
    ):

        question_text = (
            result["original_question"]
            .rstrip("?")
            .strip()
        )

        combined_parts.append(
            f"**{number}. {question_text}**\n\n"
            f"{result['answer']}"
        )

    return "\n\n---\n\n".join(
        combined_parts
    )


# =========================================================
# MAIN FINANCIAL RAG FUNCTION
# =========================================================

def ask_financial_rag(
    question,
    previous_question=None,
):
    """
    Main entry point for the Financial RAG chatbot.

    Pipeline:

        User question
              ↓
        Split multiple questions
              ↓
        Resolve follow-up context
              ↓
        Query classification
              ↓
        ┌──────────────────────┐
        │ Calculation          │
        │ OR                   │
        │ Retrieval            │
        └──────────────────────┘
              ↓
        Groq explanation
              ↓
        Answer + evidence
    """

    questions = split_questions(
        question
    )

    if not questions:

        return {
            "answer": (
                "Please enter a financial question."
            ),
            "route": "none",
            "sources": [],
            "questions": [],
        }

    # -----------------------------------------------------
    # Load and clean the dataset once for this request.
    # -----------------------------------------------------

    data = clean_data(
        load_data()
    )

    question_results = []

    current_previous_question = (
        previous_question
    )

    # -----------------------------------------------------
    # Process each individual question.
    # -----------------------------------------------------

    for individual_question in questions:

        # -------------------------------------------------
        # Resolve contextual follow-up.
        # -------------------------------------------------

        resolved_question = (
            resolve_follow_up_question(
                individual_question,
                current_previous_question,
            )
        )

        # -------------------------------------------------
        # Answer the resolved question.
        # -------------------------------------------------

        result = answer_single_question(
            resolved_question,
            data,
        )

        # -------------------------------------------------
        # Preserve both original and resolved wording.
        # -------------------------------------------------

        result["original_question"] = (
            individual_question
        )

        result["resolved_question"] = (
            resolved_question
        )

        question_results.append(
            result
        )

        # -------------------------------------------------
        # The resolved question becomes the context for
        # the next question.
        # -------------------------------------------------

        current_previous_question = (
            resolved_question
        )

    # -----------------------------------------------------
    # Combine answers.
    # -----------------------------------------------------

    combined_answer = combine_answers(
        question_results
    )

    # -----------------------------------------------------
    # Build source/evidence structure.
    # -----------------------------------------------------

    all_sources = []

    for result in question_results:

        all_sources.append(
            {
                "question": result[
                    "original_question"
                ],
                "resolved_question": result[
                    "resolved_question"
                ],
                "route": result[
                    "route"
                ],
                "sources": result[
                    "sources"
                ],
            }
        )

    # -----------------------------------------------------
    # Determine overall route.
    # -----------------------------------------------------

    routes = [
        result["route"]
        for result in question_results
    ]

    unique_routes = list(
        dict.fromkeys(routes)
    )

    if len(unique_routes) == 1:

        overall_route = (
            unique_routes[0]
        )

    else:

        overall_route = "multi"

    # -----------------------------------------------------
    # Final response object.
    # -----------------------------------------------------

    return {
        "answer": combined_answer,
        "route": overall_route,
        "sources": all_sources,
        "questions": question_results,
    }


# =========================================================
# LOCAL TEST
# =========================================================

if __name__ == "__main__":

    print("\n" + "=" * 80)
    print("RAG CHAIN TEST")
    print("=" * 80)

    test_question = (
        "What was the total revenue in 2026?"
    )

    print("\nQUESTION:")
    print(test_question)

    print("\nCalling Financial RAG...")

    result = ask_financial_rag(
        test_question
    )

    print("\n" + "-" * 80)
    print("ANSWER:")
    print(result["answer"])

    print("\n" + "-" * 80)
    print("ROUTE:")
    print(result["route"])

    print("\n" + "-" * 80)
    print("SOURCES:")
    print(result["sources"])

    print("\n" + "=" * 80)
    print("RAG CHAIN TEST COMPLETE")
    print("=" * 80)