import re

from src.calculations import (
    calculate_annual_kpis,
    calculate_annual_kpi_for_year,
    calculate_customer_ranking,
    calculate_lowest_customer_ranking,
    calculate_customer_growth,
    calculate_specific_customer_growth,
    calculate_yearly_growth,
    calculate_segment_performance,
    calculate_highest_segment_revenue,
    calculate_lowest_segment_revenue,
    calculate_region_performance,
    calculate_highest_region_revenue,
    calculate_lowest_region_revenue,
    calculate_appliance_repair_performance,
    calculate_lowest_appliance_repair_margin,
    calculate_highest_appliance_repair_margin,
    calculate_lowest_appliance_repair_revenue,
    calculate_highest_appliance_repair_revenue,
    calculate_warranty_performance,
    calculate_declining_customers,
    calculate_declining_customers_high_repair_cost,
)


# =========================================================
# YEAR EXTRACTION
# =========================================================

def extract_year(question, default=2026):
    """
    Extract the first supported dataset year from a question.
    """

    years = re.findall(
        r"\b(2024|2025|2026)\b",
        question
    )

    if years:
        return int(years[0])

    return default


def extract_years(
    question,
    defaults=(2025, 2026)
):
    """
    Extract two years from a question.

    If two years are explicitly present, return them.

    If only one year is present:
        "from 2024" -> 2024 -> 2025
        "after 2024" -> 2024 -> 2025
        "to 2026" -> 2025 -> 2026
    """

    years = re.findall(
        r"\b(2024|2025|2026)\b",
        question
    )

    if len(years) >= 2:
        return (
            int(years[0]),
            int(years[1])
        )

    if len(years) == 1:

        year = int(years[0])
        question_lower = question.lower()

        if re.search(
            r"\bfrom\s+(2024|2025|2026)\b",
            question_lower
        ):

            if year == 2024:
                return (2024, 2025)

            if year == 2025:
                return (2025, 2026)

            return defaults

        if re.search(
            r"\bafter\s+(2024|2025|2026)\b",
            question_lower
        ):

            if year == 2024:
                return (2024, 2025)

            if year == 2025:
                return (2025, 2026)

            return defaults

        if re.search(
            r"\bto\s+(2024|2025|2026)\b",
            question_lower
        ):

            if year == 2025:
                return (2024, 2025)

            if year == 2026:
                return (2025, 2026)

            return defaults

    return defaults


# =========================================================
# CUSTOMER ID
# =========================================================

def extract_customer_id(question):
    """
    Extract a customer ID such as C0062.
    """

    match = re.search(
        r"\bC\d{4}\b",
        question.upper()
    )

    if match:
        return match.group(0)

    return None


# =========================================================
# INTENT HELPERS
# =========================================================

def contains_any(text, words):
    return any(
        word in text
        for word in words
    )


def is_highest_question(question):
    return contains_any(
        question,
        [
            "highest",
            "top",
            "most",
            "best",
            "maximum",
            "max",
        ]
    )


def is_lowest_question(question):
    return contains_any(
        question,
        [
            "lowest",
            "least",
            "worst",
            "minimum",
            "min",
        ]
    )


def is_margin_question(question):
    return contains_any(
        question,
        [
            "gross margin",
            "margin",
            "profitability",
            "profitable",
        ]
    )


def is_revenue_question(question):
    return "revenue" in question


def is_profit_question(question):
    return contains_any(
        question,
        [
            "gross profit",
            "profit",
        ]
    )


def is_cost_question(question):
    return contains_any(
        question,
        [
            "direct cost",
            "direct costs",
            "cost",
            "costs",
        ]
    )


# =========================================================
# CUSTOMER-SPECIFIC REVENUE LOOKUP
# =========================================================

def calculate_customer_revenue_lookup(
    data,
    customer_id,
    year,
):
    """
    Retrieve the verified annual revenue for one customer
    from Customer_Year_Summary.
    """

    df = data["Customer_Year_Summary"].copy()

    df["Year"] = df["Year"].astype(int)

    result = df[
        (df["Customer_ID"].astype(str) == customer_id)
        & (df["Year"] == year)
    ].copy()

    if result.empty:
        return {
            "customer_id": customer_id,
            "year": year,
            "revenue_inr": None,
            "available": False,
        }

    row = result.iloc[0]

    return {
        "customer_id": customer_id,
        "year": year,
        "customer_type": row["Customer_Type"],
        "business_segment": row["Business_Segment"],
        "region": row["Region"],
        "revenue_inr": float(row["Revenue_INR"]),
        "direct_cost_inr": float(row["Direct_Cost_INR"]),
        "gross_profit_inr": float(row["Gross_Profit_INR"]),
        "service_count": int(row["Service_Count"]),
        "warranty_revenue_inr": float(
            row["Warranty_Revenue_INR"]
        ),
        "gross_margin_pct": float(
            row["Gross_Margin_Pct"]
        ),
        "available": True,
    }


# =========================================================
# MULTI-YEAR ANNUAL REVENUE
# =========================================================

def calculate_annual_revenue_by_year(
    data,
    start_year,
    end_year,
):
    """
    Return total revenue for every year in the requested
    inclusive period using Annual_KPIs.
    """

    df = data["Annual_KPIs"].copy()

    df["Year"] = df["Year"].astype(int)

    filtered = df[
        (df["Year"] >= start_year)
        & (df["Year"] <= end_year)
    ].sort_values("Year")

    results = []

    for _, row in filtered.iterrows():

        results.append(
            {
                "year": int(row["Year"]),
                "revenue_inr": float(
                    row["Revenue_INR"]
                ),
            }
        )

    return results


# =========================================================
# CUSTOMER GROSS MARGIN TREND
# =========================================================

def calculate_customer_margin_trend(
    data,
    customer_id,
    start_year,
    end_year,
):
    """
    Return annual gross margins for a customer between
    two requested years.
    """

    df = data["Customer_Year_Summary"].copy()

    df["Year"] = df["Year"].astype(int)

    result = df[
        (df["Customer_ID"].astype(str) == customer_id)
        & (
            df["Year"].isin(
                [start_year, end_year]
            )
        )
    ].copy()

    result = result.sort_values("Year")

    margins = {}

    for _, row in result.iterrows():

        margins[int(row["Year"])] = float(
            row["Gross_Margin_Pct"]
        )

    start_margin = margins.get(start_year)
    end_margin = margins.get(end_year)

    change = None

    if (
        start_margin is not None
        and end_margin is not None
    ):
        change = end_margin - start_margin

    return {
        "customer_id": customer_id,
        "start_year": start_year,
        "end_year": end_year,
        "start_margin_pct": start_margin,
        "end_margin_pct": end_margin,
        "margin_change_percentage_points": change,
        "available": (
            start_margin is not None
            and end_margin is not None
        ),
    }


# =========================================================
# MAIN CALCULATION ROUTER
# =========================================================

def answer_calculation_query(
    question,
    data
):
    """
    Route a financial question to the correct deterministic
    calculation.

    Numerical decisions are made by Pandas, not by the LLM.
    """

    question_lower = question.lower().strip()

    # =====================================================
    # COMMON WORD GROUPS
    # =====================================================

    declining_words = [
        "declining",
        "decline",
        "decreased",
        "decrease",
        "fell",
        "falling",
        "dropped",
        "drop",
        "negative growth",
        "lost revenue",
    ]

    repair_words = [
        "repair",
        "repairs",
        "breakdown repair",
        "breakdown repairs",
    ]

    high_repair_words = [
        "high repair",
        "high repair cost",
        "high repair costs",
        "highest repair",
        "expensive repair",
    ]

    change_words = [
        "change",
        "changed",
        "increase",
        "increased",
        "decrease",
        "decreased",
        "growth",
        "grew",
        "grew by",
        "decline",
        "declined",
        "difference",
        "year over year",
        "year-over-year",
        "yoy",
    ]

    # =====================================================
    # 1. MULTI-YEAR ANNUAL REVENUE TREND
    #
    # Example:
    # "What was the total revenue in each year
    #  from 2024 to 2026?"
    #
    # This must happen BEFORE the normal growth block.
    # =====================================================

    has_each_year = contains_any(
        question_lower,
        [
            "each year",
            "every year",
            "by year",
            "per year",
        ]
    )

    has_annual_revenue = (
        "revenue" in question_lower
        and (
            "total" in question_lower
            or "annual" in question_lower
        )
    )

    if has_each_year and has_annual_revenue:

        start_year, end_year = extract_years(
            question,
            defaults=(2024, 2026)
        )

        result = calculate_annual_revenue_by_year(
            data,
            start_year=start_year,
            end_year=end_year,
        )

        return {
            "type": "annual_revenue_trend",
            "question": question,
            "start_year": start_year,
            "end_year": end_year,
            "data": result,
            "calculation": (
                f"Retrieved total revenue for every year "
                f"from {start_year} through {end_year} "
                f"from Annual_KPIs."
            ),
            "source": "Annual_KPIs",
        }

    # =====================================================
    # 2. MULTI-HOP:
    #
    # DECLINING CUSTOMERS + HIGH REPAIR COSTS
    # =====================================================

    has_declining = contains_any(
        question_lower,
        declining_words
    )

    has_repair = contains_any(
        question_lower,
        repair_words
    )

    has_high_repair_cost = contains_any(
        question_lower,
        high_repair_words
    )

    if (
        has_declining
        and has_repair
        and has_high_repair_cost
    ):

        start_year, end_year = extract_years(
            question,
            defaults=(2025, 2026)
        )

        result = (
            calculate_declining_customers_high_repair_cost(
                data,
                start_year=start_year,
                end_year=end_year,
            )
        )

        return {
            "type": (
                "declining_customers_high_repair_cost"
            ),
            "question": question,
            "start_year": start_year,
            "end_year": end_year,
            "data": result,
            "calculation": (
                f"First identified Business Customers "
                f"whose revenue declined from {start_year} "
                f"to {end_year}. Then calculated their "
                f"{end_year} Breakdown Repair direct costs. "
                f"Customers were retained when their repair "
                f"direct cost was above the median repair "
                f"direct cost among the declining customers."
            ),
            "source": (
                "Customer_Year_Summary + "
                "Service_Transactions"
            ),
        }

    # =====================================================
    # 3. CUSTOMER-SPECIFIC QUESTIONS
    # =====================================================

    customer_id = extract_customer_id(
        question
    )

    if customer_id:

        # -------------------------------------------------
        # 3A. Customer gross-margin trend
        # -------------------------------------------------

        if (
            is_margin_question(question_lower)
            and contains_any(
                question_lower,
                change_words
            )
        ):

            start_year, end_year = extract_years(
                question,
                defaults=(2024, 2026)
            )

            result = calculate_customer_margin_trend(
                data,
                customer_id=customer_id,
                start_year=start_year,
                end_year=end_year,
            )

            return {
                "type": "customer_margin_trend",
                "question": question,
                "customer_id": customer_id,
                "start_year": start_year,
                "end_year": end_year,
                "data": result,
                "calculation": (
                    f"Compared gross margin for customer "
                    f"{customer_id} between {start_year} "
                    f"and {end_year} using the "
                    f"Customer_Year_Summary data."
                ),
                "source": (
                    "Customer_Year_Summary"
                ),
            }

        # -------------------------------------------------
        # 3B. Customer revenue lookup
        #
        # IMPORTANT:
        # This comes before customer growth so that:
        #
        # "What was the revenue of customer C0062 in 2026?"
        #
        # is treated as a lookup, not as a generic
        # customer question.
        # -------------------------------------------------

        if (
            is_revenue_question(question_lower)
            and not contains_any(
                question_lower,
                change_words
            )
        ):

            year = extract_year(
                question
            )

            result = calculate_customer_revenue_lookup(
                data,
                customer_id=customer_id,
                year=year,
            )

            return {
                "type": "customer_revenue_lookup",
                "question": question,
                "customer_id": customer_id,
                "year": year,
                "data": result,
                "calculation": (
                    f"Retrieved the verified annual revenue "
                    f"for customer {customer_id} in {year} "
                    f"from Customer_Year_Summary."
                ),
                "source": (
                    "Customer_Year_Summary"
                ),
            }

        # -------------------------------------------------
        # 3C. Customer year-over-year growth/change
        # -------------------------------------------------

        if contains_any(
            question_lower,
            change_words
        ):

            start_year, end_year = extract_years(
                question
            )

            result = calculate_specific_customer_growth(
                data,
                customer_id=customer_id,
                start_year=start_year,
                end_year=end_year,
            )

            return {
                "type": "customer_growth",
                "question": question,
                "customer_id": customer_id,
                "start_year": start_year,
                "end_year": end_year,
                "data": result,
                "calculation": (
                    f"Compared revenue for customer "
                    f"{customer_id} between {start_year} "
                    f"and {end_year} using the "
                    f"Customer_Year_Summary data."
                ),
                "source": (
                    "Customer_Year_Summary"
                ),
            }

    # =====================================================
    # 4. CUSTOMER RANKING
    # =====================================================

    if (
        "customer" in question_lower
        and (
            is_highest_question(question_lower)
            or is_lowest_question(question_lower)
        )
    ):

        year = extract_year(
            question
        )

        customer_type = None

        if (
            "business customer"
            in question_lower
            or "business customers"
            in question_lower
        ):
            customer_type = (
                "Business Customer"
            )

        elif (
            "residential customer"
            in question_lower
            or "residential customers"
            in question_lower
        ):
            customer_type = (
                "Residential Customer"
            )

        if is_lowest_question(
            question_lower
        ):

            result = calculate_lowest_customer_ranking(
                data,
                year=year,
                top_n=10,
                customer_type=customer_type,
            )

            ranking_type = (
                "lowest_customer_ranking"
            )

            calculation_text = (
                f"Ranked customers in {year} from "
                f"lowest to highest revenue and returned "
                f"the lowest 10 customers."
            )

        else:

            result = calculate_customer_ranking(
                data,
                year=year,
                top_n=10,
                customer_type=customer_type,
            )

            ranking_type = (
                "customer_ranking"
            )

            calculation_text = (
                f"Ranked customers in {year} from "
                f"highest to lowest revenue and returned "
                f"the top 10 customers."
            )

        return {
            "type": ranking_type,
            "question": question,
            "year": year,
            "customer_type": customer_type,
            "data": result,
            "calculation": calculation_text,
            "source": (
                "Customer_Year_Summary"
            ),
        }

    # =====================================================
    # 5. DECLINING CUSTOMERS
    # =====================================================

    if (
        "customer" in question_lower
        and has_declining
    ):

        start_year, end_year = extract_years(
            question
        )

        customer_type = None

        if (
            "business customer"
            in question_lower
            or "business customers"
            in question_lower
        ):
            customer_type = (
                "Business Customer"
            )

        elif (
            "residential customer"
            in question_lower
            or "residential customers"
            in question_lower
        ):
            customer_type = (
                "Residential Customer"
            )

        result = calculate_declining_customers(
            data,
            start_year=start_year,
            end_year=end_year,
            customer_type=customer_type,
        )

        return {
            "type": "customer_decline",
            "question": question,
            "start_year": start_year,
            "end_year": end_year,
            "customer_type": customer_type,
            "data": result,
            "calculation": (
                f"Compared customer revenue between "
                f"{start_year} and {end_year} and retained "
                f"customers whose revenue change was negative."
            ),
            "source": (
                "Customer_Year_Summary"
            ),
        }

    # =====================================================
    # 6. YEAR-OVER-YEAR REVENUE GROWTH
    # =====================================================

    if (
        contains_any(
            question_lower,
            [
                "growth",
                "change",
                "increase",
                "decrease",
                "difference",
                "year over year",
                "year-over-year",
                "yoy",
            ]
        )
        and "customer" not in question_lower
    ):

        start_year, end_year = extract_years(
            question
        )

        result = calculate_yearly_growth(
            data,
            start_year=start_year,
            end_year=end_year,
        )

        return {
            "type": "yearly_growth",
            "question": question,
            "start_year": start_year,
            "end_year": end_year,
            "data": result,
            "calculation": (
                f"Compared total annual revenue between "
                f"{start_year} and {end_year} using "
                f"Annual_KPIs."
            ),
            "source": "Annual_KPIs",
        }

    # =====================================================
    # 7. WARRANTY PERFORMANCE
    # =====================================================

    if "warranty" in question_lower:

        year = extract_year(
            question
        )

        result = calculate_warranty_performance(
            data,
            year=year,
        )

        return {
            "type": "warranty_performance",
            "question": question,
            "year": year,
            "data": result,
            "calculation": (
                f"Grouped {year} service transactions "
                f"by warranty status and calculated "
                f"revenue, direct cost, gross profit, "
                f"gross margin, revenue share, and gross "
                f"profit share."
            ),
            "source": (
                "Service_Transactions"
            ),
        }

    # =====================================================
    # 8. APPLIANCE REPAIR MARGIN
    # =====================================================

    has_appliance = (
        "appliance" in question_lower
        or "breakdown repair"
        in question_lower
    )

    if (
        has_appliance
        and is_margin_question(
            question_lower
        )
    ):

        year = extract_year(
            question
        )

        if is_lowest_question(
            question_lower
        ):

            result = (
                calculate_lowest_appliance_repair_margin(
                    data,
                    year=year,
                )
            )

            return {
                "type": (
                    "lowest_appliance_repair_margin"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated gross margin for each "
                    f"appliance's Breakdown Repair services "
                    f"in {year} and selected the appliance "
                    f"with the lowest gross margin."
                ),
                "source": (
                    "Service_Transactions"
                ),
            }

        if is_highest_question(
            question_lower
        ):

            result = (
                calculate_highest_appliance_repair_margin(
                    data,
                    year=year,
                )
            )

            return {
                "type": (
                    "highest_appliance_repair_margin"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated gross margin for each "
                    f"appliance's Breakdown Repair services "
                    f"in {year} and selected the appliance "
                    f"with the highest gross margin."
                ),
                "source": (
                    "Service_Transactions"
                ),
            }

    # =====================================================
    # 9. GENERAL APPLIANCE / REPAIR PERFORMANCE
    # =====================================================

    if (
        has_appliance
        or "repair revenue" in question_lower
        or "repair profit" in question_lower
        or "repair cost" in question_lower
    ):

        year = extract_year(
            question
        )

        if (
            is_highest_question(
                question_lower
            )
            and "revenue" in question_lower
        ):

            result = (
                calculate_highest_appliance_repair_revenue(
                    data,
                    year=year,
                )
            )

            return {
                "type": (
                    "highest_appliance_repair_revenue"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated Breakdown Repair "
                    f"revenue by appliance in {year} "
                    f"and selected the appliance with "
                    f"the highest revenue."
                ),
                "source": (
                    "Service_Transactions"
                ),
            }

        if (
            is_lowest_question(
                question_lower
            )
            and "revenue" in question_lower
        ):

            result = (
                calculate_lowest_appliance_repair_revenue(
                    data,
                    year=year,
                )
            )

            return {
                "type": (
                    "lowest_appliance_repair_revenue"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated Breakdown Repair "
                    f"revenue by appliance in {year} "
                    f"and selected the appliance with "
                    f"the lowest revenue."
                ),
                "source": (
                    "Service_Transactions"
                ),
            }

        result = (
            calculate_appliance_repair_performance(
                data,
                year=year,
            )
        )

        return {
            "type": (
                "appliance_repair_performance"
            ),
            "question": question,
            "year": year,
            "data": result,
            "calculation": (
                f"Grouped {year} Breakdown Repair "
                f"transactions by appliance and calculated "
                f"revenue, direct cost, gross profit, service "
                f"count, and gross margin."
            ),
            "source": (
                "Service_Transactions"
            ),
        }

    # =====================================================
    # 10. REGION PERFORMANCE
    # =====================================================

    if "region" in question_lower:

        year = extract_year(
            question
        )

        if (
            is_highest_question(
                question_lower
            )
            and "revenue" in question_lower
        ):

            result = calculate_highest_region_revenue(
                data,
                year=year,
            )

            return {
                "type": (
                    "highest_region_revenue"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated total revenue for each "
                    f"region in {year} and selected the "
                    f"region with the highest revenue."
                ),
                "source": (
                    "Customer_Year_Summary"
                ),
            }

        if (
            is_lowest_question(
                question_lower
            )
            and "revenue" in question_lower
        ):

            result = calculate_lowest_region_revenue(
                data,
                year=year,
            )

            return {
                "type": (
                    "lowest_region_revenue"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated total revenue for each "
                    f"region in {year} and selected the "
                    f"region with the lowest revenue."
                ),
                "source": (
                    "Customer_Year_Summary"
                ),
            }

        result = calculate_region_performance(
            data,
            year=year,
        )

        return {
            "type": "region_performance",
            "question": question,
            "year": year,
            "data": result,
            "calculation": (
                f"Grouped {year} customer-year data "
                f"by region and calculated revenue, "
                f"direct cost, gross profit, service "
                f"count, and gross margin."
            ),
            "source": (
                "Customer_Year_Summary"
            ),
        }

    # =====================================================
    # 11. BUSINESS SEGMENT PERFORMANCE
    # =====================================================

    if (
        "segment" in question_lower
        or "business segment"
        in question_lower
    ):

        year = extract_year(
            question
        )

        if (
            is_highest_question(
                question_lower
            )
            and "revenue" in question_lower
        ):

            result = calculate_highest_segment_revenue(
                data,
                year=year,
            )

            return {
                "type": (
                    "highest_segment_revenue"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated total revenue for each "
                    f"business segment in {year} and "
                    f"selected the segment with the highest "
                    f"revenue."
                ),
                "source": (
                    "Customer_Year_Summary"
                ),
            }

        if (
            is_lowest_question(
                question_lower
            )
            and "revenue" in question_lower
        ):

            result = calculate_lowest_segment_revenue(
                data,
                year=year,
            )

            return {
                "type": (
                    "lowest_segment_revenue"
                ),
                "question": question,
                "year": year,
                "data": result,
                "calculation": (
                    f"Calculated total revenue for each "
                    f"business segment in {year} and "
                    f"selected the segment with the lowest "
                    f"revenue."
                ),
                "source": (
                    "Customer_Year_Summary"
                ),
            }

        result = calculate_segment_performance(
            data,
            year=year,
        )

        return {
            "type": "segment_performance",
            "question": question,
            "year": year,
            "data": result,
            "calculation": (
                f"Grouped {year} customer-year data "
                f"by business segment and calculated "
                f"revenue, direct cost, gross profit, "
                f"service count, and gross margin."
            ),
            "source": (
                "Customer_Year_Summary"
            ),
        }

    # =====================================================
    # 12. GENERAL ANNUAL FINANCIAL QUESTION
    # =====================================================

    year = extract_year(
        question
    )

    result = calculate_annual_kpi_for_year(
        data,
        year=year,
    )

    return {
        "type": "annual_kpi",
        "question": question,
        "year": year,
        "data": result,
        "calculation": (
            f"Retrieved the verified annual KPI "
            f"record for {year} from Annual_KPIs."
        ),
        "source": "Annual_KPIs",
    }


# =========================================================
# PROCESS QUERY
# =========================================================

def process_query(
    question,
    data,
    route
):
    """
    Process a question according to the route selected
    by query_router.py.
    """

    if route == "calculation":

        return answer_calculation_query(
            question,
            data,
        )

    return {
        "type": "retrieval",
        "question": question,
        "data": None,
        "calculation": "",
        "source": "",
    }


# =========================================================
# LOCAL TEST
# =========================================================

if __name__ == "__main__":

    from src.ingestion import load_data
    from src.preprocessing import clean_data
    from src.query_router import classify_query

    data = clean_data(
        load_data()
    )

    questions = [
        "What was the total revenue in 2026?",
        "What was the gross profit in 2026?",
        "What was the gross margin in 2026?",

        "What was revenue growth from 2025 to 2026?",
        "How did revenue change between 2024 and 2026?",
        "What was revenue growth from 2024?",
        "And revenue growth from 2024?",

        "What are the top 10 business customers by 2026 revenue?",
        "Which business customers had the lowest revenue in 2026?",
        "Which business customers had declining revenue from 2025 to 2026?",
        "How much did customer C0062's revenue increase from 2025 to 2026?",

        # Fixed cases
        "What was the revenue of customer C0062 in 2026?",
        "What was the total revenue in each year from 2024 to 2026?",
        "How did customer C0062's gross margin change from 2024 to 2026?",

        "What was the warranty revenue and gross margin in 2026?",

        "Which appliance had the lowest repair margin in 2026?",
        "Which appliance had the highest repair margin in 2026?",
        "Which appliance generated the highest repair revenue in 2026?",

        "Which region generated the highest revenue in 2026?",
        "Which region generated the lowest revenue in 2026?",
        "What was the revenue by region in 2026?",

        "Which business segment generated the highest revenue in 2026?",
        "Which business segment generated the lowest revenue in 2026?",
        "What was the revenue by business segment in 2026?",

        "Which declining customers have high repair costs?",
    ]

    print("\n" + "=" * 80)
    print("QUERY ENGINE TEST")
    print("=" * 80)

    for question in questions:

        route = classify_query(
            question
        )

        result = process_query(
            question,
            data,
            route=route,
        )

        print("\n" + "-" * 80)
        print("QUESTION:")
        print(question)

        print("\nROUTE:")
        print(route)

        print("\nTYPE:")
        print(result.get("type"))

        print("\nCALCULATION:")
        print(result.get("calculation"))

        print("\nSOURCE:")
        print(result.get("source"))

        print("\nRESULT:")
        print(result.get("data"))

    print("\n" + "=" * 80)
    print("QUERY ENGINE TEST COMPLETE")
    print("=" * 80)