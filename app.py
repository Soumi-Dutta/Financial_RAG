import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.rag_chain import ask_financial_rag


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_PATH = PROJECT_ROOT / "data"

CHAT_HISTORY_PATH = DATA_PATH / "chat_history.json"


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Financial RAG Assistant",
    page_icon="💰",
    layout="wide",
)


# =========================================================
# UI STYLING
# =========================================================

st.markdown(
    """
    <style>

    /* =================================================
       TEXT SELECTION
       ================================================= */

    .stChatMessage,
    .stChatMessage * {
        user-select: text !important;
        -webkit-user-select: text !important;
    }

    .stChatMessage {
        cursor: text !important;
        overflow-wrap: anywhere;
        word-break: normal;
    }

    .stChatMessage * {
        cursor: text;
    }


    /* =================================================
       TABLE SELECTION
       ================================================= */

    .stChatMessage table,
    .stChatMessage table td,
    .stChatMessage table th {
        user-select: text !important;
        -webkit-user-select: text !important;
        cursor: text !important;
    }


    /* =================================================
       CODE / SOURCE RECORD SELECTION
       ================================================= */

    .stChatMessage pre,
    .stChatMessage code {
        white-space: pre-wrap !important;
        overflow-x: auto !important;
        user-select: text !important;
        -webkit-user-select: text !important;
        cursor: text !important;
    }


    /* =================================================
       NORMAL PAGE SCROLLING
       ================================================= */

    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
    }

    [data-testid="stMain"] {
        overflow: visible !important;
    }


    /* =================================================
       MAIN CHAT AREA
       ================================================= */

    .block-container {
        padding-bottom: 7rem;
    }


    /* =================================================
       SIDEBAR
       ================================================= */

    [data-testid="stSidebar"] {
        overflow-y: auto;
    }


    /* =================================================
       CHAT INPUT
       ================================================= */

    [data-testid="stChatInput"] {
        margin-bottom: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CHAT HISTORY FUNCTIONS
# =========================================================

def ensure_chat_history_file():
    """
    Create the chat history directory and JSON file
    if they do not already exist.
    """

    DATA_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not CHAT_HISTORY_PATH.exists():

        with open(
            CHAT_HISTORY_PATH,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                {},
                file,
                indent=2,
                ensure_ascii=False,
            )


def load_chat_history():
    """
    Load all saved conversations from the local
    JSON history file.
    """

    ensure_chat_history_file()

    try:

        with open(
            CHAT_HISTORY_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            history = json.load(file)

        if isinstance(history, dict):
            return history

        return {}

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return {}


def save_chat_history(history):
    """
    Save all conversations to the local JSON file.
    """

    ensure_chat_history_file()

    temporary_path = CHAT_HISTORY_PATH.with_suffix(
        ".tmp"
    )

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            history,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temporary_path.replace(
        CHAT_HISTORY_PATH
    )


def create_chat_title(question):
    """
    Create a short readable title from the first
    user question.
    """

    title = question.strip()

    if not title:
        return "New Chat"

    if len(title) <= 55:
        return title

    return title[:52].rstrip() + "..."


def save_current_chat():
    """
    Save the current conversation to chat history.
    """

    if not st.session_state.messages:
        return

    history = load_chat_history()

    existing_chat = history.get(
        st.session_state.chat_id,
        {},
    )

    title = existing_chat.get(
        "title",
        "New Chat",
    )

    if title == "New Chat":

        for message in st.session_state.messages:

            if message.get("role") == "user":

                title = create_chat_title(
                    message.get(
                        "content",
                        "",
                    )
                )

                break

    history[st.session_state.chat_id] = {
        "chat_id": st.session_state.chat_id,
        "title": title,
        "created_at": existing_chat.get(
            "created_at",
            datetime.now().isoformat(
                timespec="seconds"
            ),
        ),
        "updated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "messages": st.session_state.messages,
    }

    save_chat_history(history)


def load_chat(chat_id):
    """
    Load one saved conversation into the
    current Streamlit session.
    """

    history = load_chat_history()

    chat = history.get(chat_id)

    if not chat:
        return False

    st.session_state.chat_id = chat_id

    st.session_state.messages = chat.get(
        "messages",
        [],
    )

    st.session_state.pending_question = None

    return True


def delete_chat(chat_id):
    """
    Delete one specific saved conversation.

    This does not delete any other conversations.
    """

    history = load_chat_history()

    if chat_id not in history:
        return

    del history[chat_id]

    save_chat_history(history)


def start_new_chat():
    """
    Start a completely new conversation.
    """

    save_current_chat()

    st.session_state.chat_id = str(
        uuid.uuid4()
    )

    st.session_state.messages = []

    st.session_state.pending_question = None


# =========================================================
# INITIALIZE SESSION
# =========================================================

ensure_chat_history_file()

if "chat_id" not in st.session_state:

    st.session_state.chat_id = str(
        uuid.uuid4()
    )

if "messages" not in st.session_state:

    st.session_state.messages = []

if "pending_question" not in st.session_state:

    st.session_state.pending_question = None


# =========================================================
# SOURCE DISPLAY
# =========================================================

def display_sources(
    sources,
    route,
):
    """
    Display calculation or retrieval evidence.
    """

    with st.expander(
        "📚 Sources & Evidence",
        expanded=False,
    ):

        st.write(
            f"**Query route:** `{route}`"
        )

        if not sources:

            st.info(
                "No additional source details were returned."
            )

            return

        # -------------------------------------------------
        # Multiple question results
        # -------------------------------------------------

        for number, source_group in enumerate(
            sources,
            start=1,
        ):

            # A source group contains:
            # question
            # resolved_question
            # route
            # sources

            if (
                "sources" in source_group
                and "question" in source_group
            ):

                original_question = (
                    source_group.get(
                        "question",
                        "",
                    )
                )

                resolved_question = (
                    source_group.get(
                        "resolved_question",
                        "",
                    )
                )

                source_route = (
                    source_group.get(
                        "route",
                        "",
                    )
                )

                st.markdown(
                    f"### Question {number}"
                )

                st.write(
                    f"**Question:** "
                    f"{original_question}"
                )

                if (
                    resolved_question
                    != original_question
                ):

                    st.write(
                        f"**Resolved question:** "
                        f"{resolved_question}"
                    )

                st.write(
                    f"**Route:** "
                    f"`{source_route}`"
                )

                nested_sources = (
                    source_group.get(
                        "sources",
                        [],
                    )
                )

                if not nested_sources:

                    st.info(
                        "No source records were returned."
                    )

                    continue

                for source_number, source in enumerate(
                    nested_sources,
                    start=1,
                ):

                    st.markdown(
                        f"#### Evidence {number}.{source_number}"
                    )

                    display_single_source(
                        source
                    )

            else:

                st.markdown(
                    f"### Evidence {number}"
                )

                display_single_source(
                    source
                )


def display_single_source(source):
    """
    Display one calculation or retrieval source.
    """

    # =====================================================
    # CALCULATION SOURCE
    # =====================================================

    if "type" in source:

        calculation_type = source.get(
            "type",
            "N/A",
        )

        source_name = source.get(
            "source",
            "N/A",
        )

        calculation = source.get(
            "calculation",
            "",
        )

        verified_data = source.get(
            "verified_data",
            "",
        )

        st.write(
            f"**Calculation type:** "
            f"`{calculation_type}`"
        )

        st.write(
            f"**Source data:** "
            f"`{source_name}`"
        )

        if calculation:

            st.write(
                "**Calculation logic:**"
            )

            st.info(
                calculation
            )

        if verified_data:

            st.write(
                "**Verified result from dataset:**"
            )

            st.code(
                verified_data,
                language="text",
            )

        return

    # =====================================================
    # RETRIEVAL SOURCE
    # =====================================================

    metadata = source.get(
        "metadata",
        {},
    )

    if metadata:

        st.write(
            "**Metadata:**"
        )

        st.json(
            metadata
        )

    distance = source.get(
        "distance"
    )

    if distance is not None:

        st.write(
            f"**Retrieval distance:** "
            f"{distance:.4f}"
        )

    source_text = source.get(
        "text"
    )

    if source_text:

        st.write(
            "**Retrieved record:**"
        )

        st.code(
            source_text,
            language="text",
        )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    # =====================================================
    # NEW CHAT
    # =====================================================

    if st.button(
        "➕ New Chat",
        use_container_width=True,
    ):

        start_new_chat()

        st.rerun()

    st.divider()

    # =====================================================
    # CHAT HISTORY
    # =====================================================

    st.header(
        "💬 Chat History"
    )

    history = load_chat_history()

    if not history:

        st.caption(
            "No previous chats yet."
        )

    else:

        sorted_chats = sorted(
            history.values(),
            key=lambda chat: chat.get(
                "updated_at",
                "",
            ),
            reverse=True,
        )

        for chat in sorted_chats:

            chat_id = chat.get(
                "chat_id"
            )

            title = chat.get(
                "title",
                "Untitled Chat",
            )

            chat_column, delete_column = st.columns(
                [5, 1]
            )

            with chat_column:

                if st.button(
                    title,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                ):

                    if load_chat(chat_id):

                        st.rerun()

            with delete_column:

                if st.button(
                    "✕",
                    key=f"delete_{chat_id}",
                    help="Delete this chat",
                    use_container_width=True,
                ):

                    delete_chat(chat_id)

                    if (
                        st.session_state.chat_id
                        == chat_id
                    ):

                        st.session_state.chat_id = str(
                        uuid.uuid4()
                        )

                        st.session_state.messages = []

                        st.session_state.pending_question = None

                    st.rerun()

    st.divider()

    # =====================================================
    # SUGGESTED QUESTIONS
    # =====================================================

    st.header(
        "Suggested Questions"
    )

    suggested_questions = [
        "What was the total revenue in 2026?",
        "What are the top 10 business customers by 2026 revenue?",
        "Which business customers had declining revenue from 2025 to 2026?",
        "What was revenue growth from 2025 to 2026?",
        "How does warranty affect profitability?",
        "Which appliance had the highest repair revenue in 2026?",
        "Which declining customers have high repair costs?",
        "Tell me about customer C0062",
    ]

    for question in suggested_questions:

        if st.button(
            question,
            use_container_width=True,
        ):

            st.session_state.pending_question = (
                question
            )

            st.rerun()


# =========================================================
# MAIN PAGE
# =========================================================

st.title(
    "💰 Financial RAG Assistant"
)

st.caption(
    "A basic financial RAG proof-of-concept using synthetic "
    "appliance and service-centre data. "
    "All financial answers are based on the synthetic POC dataset."
)


# =========================================================
# DISPLAY CURRENT CHAT
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if message["role"] == "assistant":

            sources = message.get(
                "sources",
                [],
            )

            route = message.get(
                "route"
            )

            if route:

                display_sources(
                    sources,
                    route,
                )


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask a financial question..."
)


# =========================================================
# SUGGESTED QUESTION CLICK
# =========================================================

if st.session_state.pending_question:

    question = (
        st.session_state.pending_question
    )

    st.session_state.pending_question = None


# =========================================================
# HANDLE QUESTION
# =========================================================

if question:

    question = question.strip()

    if not question:

        st.warning(
            "Please enter a financial question."
        )

        st.stop()

    # -----------------------------------------------------
    # Display user message.
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    save_current_chat()

    with st.chat_message(
        "user"
    ):

        st.markdown(
            question
        )

    # -----------------------------------------------------
    # Generate assistant response.
    # -----------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Analyzing the financial data..."
        ):

            try:

                # -----------------------------------------
                # Find the previous user question.
                # -----------------------------------------

                previous_question = None

                for previous_message in reversed(
                    st.session_state.messages[:-1]
                ):

                    if (
                        previous_message.get(
                            "role"
                        )
                        == "user"
                    ):

                        previous_question = (
                            previous_message.get(
                                "content",
                                "",
                            )
                        )

                        break

                # -----------------------------------------
                # Ask the Financial RAG pipeline.
                # -----------------------------------------

                result = ask_financial_rag(
                    question,
                    previous_question=previous_question,
                )

                answer = result.get(
                    "answer",
                    "I could not generate an answer.",
                )

                route = result.get(
                    "route"
                )

                sources = result.get(
                    "sources",
                    [],
                )

                # -----------------------------------------
                # Display answer.
                # -----------------------------------------

                st.markdown(
                    answer
                )

                # -----------------------------------------
                # Display source evidence.
                # -----------------------------------------

                if route:

                    display_sources(
                        sources,
                        route,
                    )

                # -----------------------------------------
                # Save assistant message.
                # -----------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "route": route,
                        "sources": sources,
                    }
                )

                save_current_chat()

                # -----------------------------------------
                # Refresh the application.
                # -----------------------------------------

                st.rerun()

            except Exception as error:

                error_message = (
                    "Something went wrong while processing "
                    "the question."
                )

                st.error(
                    error_message
                )

                with st.expander(
                    "Technical error"
                ):

                    st.exception(
                        error
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "route": "error",
                        "sources": [],
                    }
                )

                save_current_chat()

                st.rerun()