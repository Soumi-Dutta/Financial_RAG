import re


# ---------------------------------------------------------
# FOLLOW-UP QUESTION DETECTION
# ---------------------------------------------------------

def is_follow_up_question(query):
    """
    Detect questions that may depend on the previous question.

    Examples:
        How about 2025?
        What about 2024?
        And 2025?
        And the gross profit?
        What about warranty revenue?
        Same for 2025?
    """

    query = query.lower().strip()

    follow_up_patterns = [
        r"^how about\b",
        r"^what about\b",
        r"^and\b",
        r"^same\b",
    ]

    return any(
        re.search(pattern, query)
        for pattern in follow_up_patterns
    )


# ---------------------------------------------------------
# CALCULATION KEYWORDS
# ---------------------------------------------------------

CALCULATION_KEYWORDS = [
    # General financial measures
    "revenue",
    "cost",
    "profit",
    "gross profit",
    "gross margin",
    "margin",
    "growth",
    "total",
    "average",
    "count",
    "how many",

    # Repair
    "repair revenue",
    "repair cost",
    "repair profit",
    "repair margin",
    "repair profitability",
    "breakdown repair",
    "breakdown repair revenue",
    "breakdown repair cost",
    "breakdown repair profit",
    "breakdown repair margin",
    "breakdown repair profitability",

    # Warranty
    "warranty",
    "warranty revenue",
    "warranty cost",
    "warranty profit",
    "warranty margin",
    "warranty profitability",

    # Customers
    "top customer",
    "top customers",
    "highest customer",
    "highest customers",
    "lowest customer",
    "lowest customers",
    "best customer",
    "worst customer",
    "rank customer",
    "rank customers",
    "ranking customer",
    "ranking customers",
    "declining customer",
    "declining customers",
    "customer growth",
    "customer revenue",
    "customer profit",
    "customer margin",

    # Business segments
    "business segment",
    "business segments",
    "segment",
    "segments",
    "segment revenue",
    "segment profit",
    "segment margin",
    "segment growth",

    # Regions
    "region",
    "regions",
    "regional",
    "region revenue",
    "region profit",
    "region margin",
    "region growth",

    # Appliance performance
    "appliance performance",
    "appliance revenue",
    "appliance cost",
    "appliance profit",
    "appliance margin",
    "appliance profitability",
    "repair performance by appliance",
    "appliance repair",
    "appliance repair revenue",
    "appliance repair cost",
    "appliance repair profit",
    "appliance repair margin",
    "appliance repair profitability",

    # Time comparisons
    "year over year",
    "year-over-year",
    "yoy",
    "growth from",
    "growth between",
    "change from",
    "change between",
    "increase from",
    "decrease from",
    "decline from",
]


# ---------------------------------------------------------
# CHECK FOR CALCULATION QUESTION
# ---------------------------------------------------------

def contains_calculation_keyword(query):
    """
    Return True when the question asks for a numerical,
    financial, ranking, comparison, trend, or performance
    calculation.
    """

    query = query.lower().strip()

    return any(
        keyword in query
        for keyword in CALCULATION_KEYWORDS
    )


# ---------------------------------------------------------
# EXTRACT YEAR
# ---------------------------------------------------------

def extract_year(query):
    """
    Extract the first four-digit year such as 2024, 2025,
    or 2026 from a question.

    Returns:
        str or None
    """

    match = re.search(
        r"\b(20\d{2})\b",
        query,
    )

    if match:
        return match.group(1)

    return None


# ---------------------------------------------------------
# REMOVE YEAR FROM QUESTION
# ---------------------------------------------------------

def remove_year(query):
    """
    Remove a four-digit year from a question.

    Used when we need to compare the structure of two
    questions without treating the year as the main subject.
    """

    return re.sub(
        r"\b20\d{2}\b",
        "",
        query,
    ).strip()


# ---------------------------------------------------------
# FOLLOW-UP QUESTION RESOLUTION
# ---------------------------------------------------------

def resolve_follow_up_question(current_question, previous_question):
    """
    Convert a contextual follow-up question into a standalone
    question whenever the previous question provides useful
    context.

    Examples:

        Previous:
            What was the total revenue in 2026?

        Current:
            How about 2025?

        Result:
            What was the total revenue in 2025?


        Previous:
            What was the total revenue in 2026?

        Current:
            And the gross profit?

        Result:
            What was the gross profit in 2026?


        Previous:
            How about 2025?

        Current:
            And revenue growth from 2024?

        Result:
            And revenue growth from 2024?

    The last example remains unchanged because it introduces
    a new explicit calculation and a new year.
    """

    if not previous_question:
        return current_question

    current_question = current_question.strip()
    previous_question = previous_question.strip()

    if not current_question:
        return current_question

    if not is_follow_up_question(current_question):
        return current_question

    current_lower = current_question.lower()

    previous_year = extract_year(previous_question)
    current_year = extract_year(current_question)

    # -----------------------------------------------------
    # CASE 1:
    # Explicit new calculation with its own year.
    #
    # Example:
    #   Previous: How about 2025?
    #   Current:  And revenue growth from 2024?
    #
    # Do not inherit the previous question.
    # -----------------------------------------------------

    if (
        current_year is not None
        and contains_calculation_keyword(current_question)
    ):
        return current_question

    # -----------------------------------------------------
    # CASE 2:
    # Follow-up contains only a new year.
    #
    # Example:
    #   Previous: What was total revenue in 2026?
    #   Current:  How about 2025?
    #
    # Replace the previous year.
    # -----------------------------------------------------

    if current_year is not None:

        if previous_year is not None:
            resolved = re.sub(
                r"\b20\d{2}\b",
                current_year,
                previous_question,
                count=1,
            )

            return resolved

        return (
            previous_question.rstrip("?").strip()
            + f" in {current_year}?"
        )

    # -----------------------------------------------------
    # CASE 3:
    # Follow-up introduces a different calculation but
    # doesn't specify a year.
    #
    # Example:
    #   Previous: What was total revenue in 2026?
    #   Current:  And the gross profit?
    #
    # Carry forward the previous year's context.
    # -----------------------------------------------------

    if contains_calculation_keyword(current_question):

        if previous_year is not None:

            cleaned_current = current_question.rstrip("?").strip()

            return (
                cleaned_current
                + f" in {previous_year}?"
            )

        return current_question

    # -----------------------------------------------------
    # CASE 4:
    # Follow-up does not contain an obvious calculation.
    #
    # Keep it unchanged rather than inventing context.
    # -----------------------------------------------------

    return current_question


# ---------------------------------------------------------
# QUESTION SPLITTING
# ---------------------------------------------------------

def split_questions(message):
    """
    Split a user message into individual questions.

    Examples:

        What was revenue in 2026?
        How about 2025?

    becomes:

        [
            "What was revenue in 2026?",
            "How about 2025?"
        ]


        What was revenue in 2026? What was gross profit in 2026?

    becomes two separate questions.

    A normal single question remains unchanged.
    """

    message = message.strip()

    if not message:
        return []

    # -----------------------------------------------------
    # Split on question marks.
    # -----------------------------------------------------

    parts = re.split(
        r"\?\s*",
        message,
    )

    questions = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        # Remove accidental trailing punctuation.
        part = re.sub(
            r"[.!,;:]+$",
            "",
            part,
        ).strip()

        if not part:
            continue

        questions.append(
            part + "?"
        )

    return questions


# ---------------------------------------------------------
# CUSTOMER RANKING DETECTION
# ---------------------------------------------------------

def is_customer_ranking_question(query):
    """
    Detect customer ranking questions.

    Examples:
        Which business customers had the highest revenue?
        What are the top 10 customers?
        Which customers had the lowest gross margin?
    """

    query = query.lower().strip()

    customer_words = [
        "customer",
        "customers",
    ]

    ranking_words = [
        "top",
        "highest",
        "lowest",
        "most",
        "least",
        "rank",
        "ranking",
        "best",
        "worst",
    ]

    has_customer = any(
        word in query
        for word in customer_words
    )

    has_ranking_word = any(
        word in query
        for word in ranking_words
    )

    return (
        has_customer
        and has_ranking_word
    )


# ---------------------------------------------------------
# APPLIANCE PERFORMANCE DETECTION
# ---------------------------------------------------------

def is_appliance_performance_question(query):
    """
    Detect appliance/service performance questions.

    These should generally use the deterministic calculation
    layer because they can require grouping and comparison.
    """

    query = query.lower().strip()

    appliance_words = [
        "appliance",
        "appliances",
        "tv",
        "washing machine",
        "ac",
        "refrigerator",
        "water purifier",
        "microwave",
    ]

    performance_words = [
        "performance",
        "revenue",
        "cost",
        "profit",
        "margin",
        "margin",
        "profitability",
        "highest",
        "lowest",
        "best",
        "worst",
        "top",
    ]

    has_appliance = any(
        word in query
        for word in appliance_words
    )

    has_performance = any(
        word in query
        for word in performance_words
    )

    return (
        has_appliance
        and has_performance
    )


# ---------------------------------------------------------
# QUERY CLASSIFICATION
# ---------------------------------------------------------

def classify_query(query):
    """
    Classify a question into:

        calculation
        retrieval

    Numerical, ranking, comparison, trend, and performance
    questions go to the deterministic calculation layer.

    Other questions go to semantic RAG retrieval.
    """

    query = query.lower().strip()

    if not query:
        return "retrieval"

    # -----------------------------------------------------
    # Customer ranking
    # -----------------------------------------------------

    if is_customer_ranking_question(query):
        return "calculation"

    # -----------------------------------------------------
    # Appliance performance
    # -----------------------------------------------------

    if is_appliance_performance_question(query):
        return "calculation"

    # -----------------------------------------------------
    # General calculation keywords
    # -----------------------------------------------------

    if contains_calculation_keyword(query):
        return "calculation"

    # -----------------------------------------------------
    # Explicit comparison language
    # -----------------------------------------------------

    comparison_patterns = [
        r"\bcompare\b",
        r"\bcomparison\b",
        r"\bversus\b",
        r"\bvs\.?\b",
        r"\bchange\b",
        r"\bincrease\b",
        r"\bdecrease\b",
        r"\bdeclin(?:e|ed|ing)\b",
    ]

    if any(
        re.search(pattern, query)
        for pattern in comparison_patterns
    ):
        return "calculation"

    # -----------------------------------------------------
    # Default
    # -----------------------------------------------------

    return "retrieval"


# ---------------------------------------------------------
# SIMPLE LOCAL TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    test_questions = [
        "What was the total revenue in 2026?",
        "How about 2025?",
        "And the gross profit?",
        "And revenue growth from 2024?",
        "Which business customers had the highest revenue in 2026?",
        "Which appliance had the lowest repair margin in 2026?",
        "What was the warranty revenue in 2026?",
        "Which region generated the highest revenue in 2026?",
        "Tell me about the service records for customer C0062.",
    ]

    previous = None

    print("\nQUESTION ROUTER TEST\n")
    print("-" * 70)

    for question in test_questions:

        resolved = resolve_follow_up_question(
            question,
            previous,
        )

        route = classify_query(
            resolved
        )

        print(f"Original : {question}")
        print(f"Resolved : {resolved}")
        print(f"Route    : {route}")
        print("-" * 70)

        previous = resolved