import pandas as pd


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def _calculate_margin(gross_profit, revenue):
    """
    Safely calculate gross margin percentage.
    """

    return (
        gross_profit
        / revenue.replace(0, pd.NA)
        * 100
    )


def _filter_year(df, year):
    """
    Return rows belonging to the requested year.
    """

    return df[df["Year"] == year].copy()


# =========================================================
# ANNUAL KPI CALCULATIONS
# =========================================================

def calculate_annual_kpis(data):
    """
    Return the annual KPI table.

    Source:
        Annual_KPIs
    """

    df = data["Annual_KPIs"].copy()

    columns = [
        "Year",
        "Revenue_INR",
        "Direct_Cost_INR",
        "Gross_Profit_INR",
        "Service_Count",
        "Warranty_Revenue_INR",
        "Customer_Charge_INR",
        "Gross_Margin_Pct",
        "Revenue_Growth_Pct",
    ]

    return df[columns].sort_values(
        "Year"
    ).reset_index(drop=True)


def calculate_annual_kpi_for_year(
    data,
    year=2026
):
    """
    Return exactly one annual KPI row for a year.

    This is useful for questions such as:

        What was the total revenue in 2026?
        What was the gross profit in 2025?
        What was the gross margin in 2026?
    """

    df = data["Annual_KPIs"].copy()

    result = df[
        df["Year"] == year
    ].copy()

    return result.reset_index(drop=True)


# =========================================================
# CUSTOMER RANKING
# =========================================================

def calculate_customer_ranking(
    data,
    year=2026,
    top_n=10,
    customer_type=None
):
    """
    Rank customers by revenue for a specific year.

    Default:
        Top 10 customers in 2026.

    The ranking is deterministic and performed entirely
    with Pandas.
    """

    df = data["Customer_Year_Summary"].copy()

    df = _filter_year(
        df,
        year
    )

    if customer_type is not None:
        df = df[
            df["Customer_Type"] == customer_type
        ]

    result = (
        df.groupby(
            [
                "Customer_ID",
                "Customer_Type",
                "Business_Segment",
                "Region",
            ],
            as_index=False
        )
        .agg(
            Revenue_INR=(
                "Revenue_INR",
                "sum"
            ),
            Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Gross_Profit_INR=(
                "Gross_Profit_INR",
                "sum"
            ),
        )
        .sort_values(
            [
                "Revenue_INR",
                "Customer_ID",
            ],
            ascending=[
                False,
                True,
            ]
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    result.insert(
        0,
        "Rank",
        range(
            1,
            len(result) + 1
        )
    )

    return result


def calculate_lowest_customer_ranking(
    data,
    year=2026,
    top_n=10,
    customer_type=None
):
    """
    Return the customers with the lowest revenue.

    This is deterministic and sorted from lowest to highest.
    """

    df = data["Customer_Year_Summary"].copy()

    df = _filter_year(
        df,
        year
    )

    if customer_type is not None:
        df = df[
            df["Customer_Type"] == customer_type
        ]

    result = (
        df.groupby(
            [
                "Customer_ID",
                "Customer_Type",
                "Business_Segment",
                "Region",
            ],
            as_index=False
        )
        .agg(
            Revenue_INR=(
                "Revenue_INR",
                "sum"
            ),
            Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Gross_Profit_INR=(
                "Gross_Profit_INR",
                "sum"
            ),
        )
        .sort_values(
            [
                "Revenue_INR",
                "Customer_ID",
            ],
            ascending=[
                True,
                True,
            ]
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    result.insert(
        0,
        "Rank",
        range(
            1,
            len(result) + 1
        )
    )

    return result


# =========================================================
# CUSTOMER GROWTH
# =========================================================

def calculate_customer_growth(
    data,
    start_year=2025,
    end_year=2026,
    customer_type="Business Customer"
):
    """
    Compare customer revenue between two years.

    Returns:
        - starting revenue
        - ending revenue
        - revenue change
        - growth percentage
        - whether revenue declined

    A zero starting revenue is represented as NA for
    percentage growth because percentage growth from zero
    is undefined.
    """

    df = data["Customer_Year_Summary"].copy()

    if customer_type is not None:
        df = df[
            df["Customer_Type"] == customer_type
        ]

    df = df[
        df["Year"].isin(
            [
                start_year,
                end_year,
            ]
        )
    ]

    pivot = df.pivot_table(
        index=[
            "Customer_ID",
            "Customer_Type",
            "Business_Segment",
            "Region",
        ],
        columns="Year",
        values="Revenue_INR",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    if start_year not in pivot.columns:
        pivot[start_year] = 0

    if end_year not in pivot.columns:
        pivot[end_year] = 0

    pivot = pivot.rename(
        columns={
            start_year:
                f"Revenue_{start_year}_INR",
            end_year:
                f"Revenue_{end_year}_INR",
        }
    )

    start_column = (
        f"Revenue_{start_year}_INR"
    )

    end_column = (
        f"Revenue_{end_year}_INR"
    )

    pivot["Revenue_Change_INR"] = (
        pivot[end_column]
        - pivot[start_column]
    )

    pivot["Revenue_Growth_Pct"] = (
        pivot["Revenue_Change_INR"]
        / pivot[start_column].replace(
            0,
            pd.NA
        )
        * 100
    )

    pivot["Declined"] = (
        pivot["Revenue_Change_INR"] < 0
    )

    pivot = pivot.sort_values(
        [
            "Revenue_Growth_Pct",
            "Customer_ID",
        ],
        ascending=[
            True,
            True,
        ],
        na_position="last"
    ).reset_index(drop=True)

    return pivot


def calculate_declining_customers(
    data,
    start_year=2025,
    end_year=2026,
    customer_type="Business Customer"
):
    """
    Return only customers whose revenue declined between
    the two requested years.
    """

    result = calculate_customer_growth(
        data,
        start_year=start_year,
        end_year=end_year,
        customer_type=customer_type
    )

    return result[
        result["Declined"] == True
    ].copy().reset_index(drop=True)


# =========================================================
# CUSTOMER-SPECIFIC GROWTH
# =========================================================

def calculate_specific_customer_growth(
    data,
    customer_id,
    start_year=2025,
    end_year=2026
):
    """
    Calculate revenue growth for one specific customer.

    Example:
        C0062 from 2025 to 2026.
    """

    df = data["Customer_Year_Summary"].copy()

    df = df[
        (
            df["Customer_ID"]
            == customer_id
        )
        & (
            df["Year"].isin(
                [
                    start_year,
                    end_year,
                ]
            )
        )
    ]

    if df.empty:
        return pd.DataFrame()

    grouped = (
        df.groupby(
            "Year",
            as_index=False
        )
        .agg(
            Revenue_INR=(
                "Revenue_INR",
                "sum"
            ),
            Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Gross_Profit_INR=(
                "Gross_Profit_INR",
                "sum"
            ),
        )
    )

    start = grouped[
        grouped["Year"] == start_year
    ]

    end = grouped[
        grouped["Year"] == end_year
    ]

    if start.empty or end.empty:
        return pd.DataFrame()

    start_revenue = start.iloc[0][
        "Revenue_INR"
    ]

    end_revenue = end.iloc[0][
        "Revenue_INR"
    ]

    revenue_change = (
        end_revenue
        - start_revenue
    )

    if start_revenue == 0:
        growth = pd.NA
    else:
        growth = (
            revenue_change
            / start_revenue
            * 100
        )

    return pd.DataFrame(
        [
            {
                "Customer_ID": customer_id,
                "Start_Year": start_year,
                "End_Year": end_year,
                "Revenue_Start_INR":
                    start_revenue,
                "Revenue_End_INR":
                    end_revenue,
                "Revenue_Change_INR":
                    revenue_change,
                "Revenue_Growth_Pct":
                    growth,
            }
        ]
    )


# =========================================================
# YEARLY GROWTH
# =========================================================

def calculate_yearly_growth(
    data,
    start_year=2025,
    end_year=2026
):
    """
    Calculate total company revenue growth between two years.
    """

    df = data["Annual_KPIs"].copy()

    start = df[
        df["Year"] == start_year
    ]

    end = df[
        df["Year"] == end_year
    ]

    if start.empty or end.empty:
        return pd.DataFrame()

    start_revenue = start.iloc[0][
        "Revenue_INR"
    ]

    end_revenue = end.iloc[0][
        "Revenue_INR"
    ]

    revenue_change = (
        end_revenue
        - start_revenue
    )

    if start_revenue == 0:
        revenue_growth = pd.NA
    else:
        revenue_growth = (
            revenue_change
            / start_revenue
            * 100
        )

    return pd.DataFrame(
        [
            {
                "Start_Year": start_year,
                "End_Year": end_year,
                "Revenue_Start_INR":
                    start_revenue,
                "Revenue_End_INR":
                    end_revenue,
                "Revenue_Change_INR":
                    revenue_change,
                "Revenue_Growth_Pct":
                    revenue_growth,
            }
        ]
    )


# =========================================================
# BUSINESS SEGMENT PERFORMANCE
# =========================================================

def calculate_segment_performance(
    data,
    year=2026
):
    """
    Calculate revenue, cost, gross profit, service count,
    and gross margin for each business segment.
    """

    df = data[
        "Customer_Year_Summary"
    ].copy()

    df = _filter_year(
        df,
        year
    )

    result = (
        df.groupby(
            "Business_Segment",
            as_index=False
        )
        .agg(
            Revenue_INR=(
                "Revenue_INR",
                "sum"
            ),
            Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Gross_Profit_INR=(
                "Gross_Profit_INR",
                "sum"
            ),
            Service_Count=(
                "Service_Count",
                "sum"
            ),
        )
    )

    result["Gross_Margin_Pct"] = (
        result["Gross_Profit_INR"]
        / result["Revenue_INR"].replace(
            0,
            pd.NA
        )
        * 100
    )

    result = result.sort_values(
        [
            "Revenue_INR",
            "Business_Segment",
        ],
        ascending=[
            False,
            True,
        ]
    ).reset_index(drop=True)

    return result


def calculate_highest_segment_revenue(
    data,
    year=2026
):
    """
    Deterministically identify the segment with the
    highest revenue.
    """

    result = calculate_segment_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    return result.head(1).copy()


def calculate_lowest_segment_revenue(
    data,
    year=2026
):
    """
    Deterministically identify the segment with the
    lowest revenue.
    """

    result = calculate_segment_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    return (
        result.sort_values(
            [
                "Revenue_INR",
                "Business_Segment",
            ],
            ascending=[
                True,
                True,
            ]
        )
        .head(1)
        .copy()
        .reset_index(drop=True)
    )


# =========================================================
# REGION PERFORMANCE
# =========================================================

def calculate_region_performance(
    data,
    year=2026
):
    """
    Calculate revenue, cost, gross profit, service count,
    and gross margin for each region.
    """

    df = data[
        "Customer_Year_Summary"
    ].copy()

    df = _filter_year(
        df,
        year
    )

    result = (
        df.groupby(
            "Region",
            as_index=False
        )
        .agg(
            Revenue_INR=(
                "Revenue_INR",
                "sum"
            ),
            Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Gross_Profit_INR=(
                "Gross_Profit_INR",
                "sum"
            ),
            Service_Count=(
                "Service_Count",
                "sum"
            ),
        )
    )

    result["Gross_Margin_Pct"] = (
        result["Gross_Profit_INR"]
        / result["Revenue_INR"].replace(
            0,
            pd.NA
        )
        * 100
    )

    result = result.sort_values(
        [
            "Revenue_INR",
            "Region",
        ],
        ascending=[
            False,
            True,
        ]
    ).reset_index(drop=True)

    return result


def calculate_highest_region_revenue(
    data,
    year=2026
):
    """
    Deterministically identify the region with the
    highest revenue.
    """

    result = calculate_region_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    return result.head(1).copy()


def calculate_lowest_region_revenue(
    data,
    year=2026
):
    """
    Deterministically identify the region with the
    lowest revenue.
    """

    result = calculate_region_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    return (
        result.sort_values(
            [
                "Revenue_INR",
                "Region",
            ],
            ascending=[
                True,
                True,
            ]
        )
        .head(1)
        .copy()
        .reset_index(drop=True)
    )


# =========================================================
# APPLIANCE BREAKDOWN REPAIR PERFORMANCE
# =========================================================

def calculate_appliance_repair_performance(
    data,
    year=2026
):
    """
    Calculate financial performance for each appliance
    type for Breakdown Repair services.
    """

    df = data[
        "Service_Transactions"
    ].copy()

    df = df[
        (
            df["Year"] == year
        )
        & (
            df["Service_Type"]
            == "Breakdown Repair"
        )
    ]

    result = (
        df.groupby(
            "Appliance_Type",
            as_index=False
        )
        .agg(
            Revenue_INR=(
                "Total_Revenue_INR",
                "sum"
            ),
            Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Gross_Profit_INR=(
                "Gross_Profit_INR",
                "sum"
            ),
            Service_Count=(
                "Service_ID",
                "count"
            ),
        )
    )

    result["Gross_Margin_Pct"] = (
        result["Gross_Profit_INR"]
        / result["Revenue_INR"].replace(
            0,
            pd.NA
        )
        * 100
    )

    result = result.sort_values(
        [
            "Revenue_INR",
            "Appliance_Type",
        ],
        ascending=[
            False,
            True,
        ]
    ).reset_index(drop=True)

    return result


def calculate_lowest_appliance_repair_margin(
    data,
    year=2026
):
    """
    Deterministically identify the appliance with the
    lowest gross margin for Breakdown Repair services.
    """

    result = calculate_appliance_repair_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    lowest_row = result.loc[
        result["Gross_Margin_Pct"].idxmin()
    ]

    return pd.DataFrame(
        [
            {
                "Year": year,
                "Appliance_Type":
                    lowest_row[
                        "Appliance_Type"
                    ],
                "Revenue_INR":
                    lowest_row[
                        "Revenue_INR"
                    ],
                "Direct_Cost_INR":
                    lowest_row[
                        "Direct_Cost_INR"
                    ],
                "Gross_Profit_INR":
                    lowest_row[
                        "Gross_Profit_INR"
                    ],
                "Service_Count":
                    lowest_row[
                        "Service_Count"
                    ],
                "Gross_Margin_Pct":
                    lowest_row[
                        "Gross_Margin_Pct"
                    ],
            }
        ]
    )


def calculate_highest_appliance_repair_margin(
    data,
    year=2026
):
    """
    Deterministically identify the appliance with the
    highest gross margin for Breakdown Repair services.
    """

    result = calculate_appliance_repair_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    highest_row = result.loc[
        result["Gross_Margin_Pct"].idxmax()
    ]

    return pd.DataFrame(
        [
            {
                "Year": year,
                "Appliance_Type":
                    highest_row[
                        "Appliance_Type"
                    ],
                "Revenue_INR":
                    highest_row[
                        "Revenue_INR"
                    ],
                "Direct_Cost_INR":
                    highest_row[
                        "Direct_Cost_INR"
                    ],
                "Gross_Profit_INR":
                    highest_row[
                        "Gross_Profit_INR"
                    ],
                "Service_Count":
                    highest_row[
                        "Service_Count"
                    ],
                "Gross_Margin_Pct":
                    highest_row[
                        "Gross_Margin_Pct"
                    ],
            }
        ]
    )


def calculate_lowest_appliance_repair_revenue(
    data,
    year=2026
):
    """
    Deterministically identify the appliance with the
    lowest Breakdown Repair revenue.
    """

    result = calculate_appliance_repair_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    return (
        result.sort_values(
            [
                "Revenue_INR",
                "Appliance_Type",
            ],
            ascending=[
                True,
                True,
            ]
        )
        .head(1)
        .copy()
        .reset_index(drop=True)
    )


def calculate_highest_appliance_repair_revenue(
    data,
    year=2026
):
    """
    Deterministically identify the appliance with the
    highest Breakdown Repair revenue.
    """

    result = calculate_appliance_repair_performance(
        data,
        year=year
    )

    if result.empty:
        return pd.DataFrame()

    return result.head(1).copy()


# =========================================================
# WARRANTY PERFORMANCE
# =========================================================

def calculate_warranty_performance(
    data,
    year=2026
):
    """
    Calculate financial performance for warranty versus
    non-warranty service transactions.
    """

    df = data[
        "Service_Transactions"
    ].copy()

    df = _filter_year(
        df,
        year
    )

    result = (
        df.groupby(
            "Under_Warranty",
            as_index=False
        )
        .agg(
            Revenue_INR=(
                "Total_Revenue_INR",
                "sum"
            ),
            Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Gross_Profit_INR=(
                "Gross_Profit_INR",
                "sum"
            ),
            Service_Count=(
                "Service_ID",
                "count"
            ),
        )
    )

    result["Gross_Margin_Pct"] = (
        result["Gross_Profit_INR"]
        / result["Revenue_INR"].replace(
            0,
            pd.NA
        )
        * 100
    )

    total_revenue = result[
        "Revenue_INR"
    ].sum()

    total_gross_profit = result[
        "Gross_Profit_INR"
    ].sum()

    if total_revenue == 0:
        result["Revenue_Share_Pct"] = 0
    else:
        result["Revenue_Share_Pct"] = (
            result["Revenue_INR"]
            / total_revenue
            * 100
        )

    if total_gross_profit == 0:
        result["Gross_Profit_Share_Pct"] = 0
    else:
        result["Gross_Profit_Share_Pct"] = (
            result["Gross_Profit_INR"]
            / total_gross_profit
            * 100
        )

    margins = result.set_index(
        "Under_Warranty"
    )["Gross_Margin_Pct"]

    warranty_margin = margins.get(
        "Yes",
        0
    )

    non_warranty_margin = margins.get(
        "No",
        0
    )

    margin_difference = (
        non_warranty_margin
        - warranty_margin
    )

    result[
        "Margin_Difference_vs_Other_Pct_Points"
    ] = abs(
        margin_difference
    )

    return result


# =========================================================
# DECLINING CUSTOMERS + HIGH REPAIR COST
# =========================================================

def calculate_declining_customers_high_repair_cost(
    data,
    start_year=2025,
    end_year=2026
):
    """
    Multi-hop calculation.

    Step 1:
        Find Business Customers whose revenue declined.

    Step 2:
        For those customers, calculate Breakdown Repair
        direct costs during the end year.

    Step 3:
        Define "high repair cost" as repair cost above
        the median repair cost among the declining customers.

    Repair cost is:
        Direct_Cost_INR
        for Breakdown Repair transactions.
    """

    # -----------------------------------------------------
    # STEP 1: DECLINING BUSINESS CUSTOMERS
    # -----------------------------------------------------

    customer_growth = calculate_customer_growth(
        data,
        start_year=start_year,
        end_year=end_year,
        customer_type="Business Customer"
    )

    declining = customer_growth[
        customer_growth["Declined"] == True
    ].copy()

    if declining.empty:
        return pd.DataFrame()

    declining_customer_ids = (
        declining[
            "Customer_ID"
        ].tolist()
    )

    # -----------------------------------------------------
    # STEP 2: BREAKDOWN REPAIR COSTS
    # -----------------------------------------------------

    transactions = data[
        "Service_Transactions"
    ].copy()

    repair_transactions = transactions[
        (
            transactions["Year"]
            == end_year
        )
        & (
            transactions["Service_Type"]
            == "Breakdown Repair"
        )
        & (
            transactions["Customer_Type"]
            == "Business Customer"
        )
        & (
            transactions["Customer_ID"].isin(
                declining_customer_ids
            )
        )
    ].copy()

    repair_costs = (
        repair_transactions
        .groupby(
            "Customer_ID",
            as_index=False
        )
        .agg(
            Repair_Direct_Cost_INR=(
                "Direct_Cost_INR",
                "sum"
            ),
            Repair_Revenue_INR=(
                "Total_Revenue_INR",
                "sum"
            ),
            Repair_Service_Count=(
                "Service_ID",
                "count"
            ),
        )
    )

    # -----------------------------------------------------
    # CUSTOMERS WITHOUT BREAKDOWN REPAIRS
    # GET ZERO VALUES
    # -----------------------------------------------------

    declining = declining.merge(
        repair_costs,
        on="Customer_ID",
        how="left"
    )

    declining[
        "Repair_Direct_Cost_INR"
    ] = declining[
        "Repair_Direct_Cost_INR"
    ].fillna(0)

    declining[
        "Repair_Revenue_INR"
    ] = declining[
        "Repair_Revenue_INR"
    ].fillna(0)

    declining[
        "Repair_Service_Count"
    ] = declining[
        "Repair_Service_Count"
    ].fillna(0)

    # -----------------------------------------------------
    # STEP 3: HIGH REPAIR COST THRESHOLD
    # -----------------------------------------------------

    median_repair_cost = (
        declining[
            "Repair_Direct_Cost_INR"
        ].median()
    )

    declining[
        "High_Repair_Cost"
    ] = (
        declining[
            "Repair_Direct_Cost_INR"
        ]
        > median_repair_cost
    )

    declining[
        "Repair_Cost_vs_Median_INR"
    ] = (
        declining[
            "Repair_Direct_Cost_INR"
        ]
        - median_repair_cost
    )

    result = declining[
        declining["High_Repair_Cost"] == True
    ].copy()

    result = result.sort_values(
        [
            "Repair_Direct_Cost_INR",
            "Customer_ID",
        ],
        ascending=[
            False,
            True,
        ]
    ).reset_index(drop=True)

    result[
        "High_Repair_Cost_Threshold_INR"
    ] = median_repair_cost

    return result


# =========================================================
# LOCAL TEST
# =========================================================

if __name__ == "__main__":

    from src.ingestion import load_data
    from src.preprocessing import clean_data

    data = load_data()
    data = clean_data(data)

    print("\n" + "=" * 70)
    print("CALCULATIONS TEST")
    print("=" * 70)

    # -----------------------------------------------------
    # ANNUAL KPI
    # -----------------------------------------------------

    print("\n2026 Annual KPI:")
    print(
        calculate_annual_kpi_for_year(
            data,
            year=2026
        )
    )

    # -----------------------------------------------------
    # CUSTOMER RANKING
    # -----------------------------------------------------

    print("\nTop Business Customers 2026:")
    print(
        calculate_customer_ranking(
            data,
            year=2026,
            top_n=10,
            customer_type="Business Customer"
        )
    )

    # -----------------------------------------------------
    # CUSTOMER GROWTH
    # -----------------------------------------------------

    print("\nCustomer Growth 2025 -> 2026:")
    print(
        calculate_customer_growth(
            data,
            start_year=2025,
            end_year=2026,
            customer_type="Business Customer"
        ).head(10)
    )

    # -----------------------------------------------------
    # SPECIFIC CUSTOMER
    # -----------------------------------------------------

    print("\nC0062 Growth 2025 -> 2026:")
    print(
        calculate_specific_customer_growth(
            data,
            customer_id="C0062",
            start_year=2025,
            end_year=2026
        )
    )

    # -----------------------------------------------------
    # YEARLY GROWTH
    # -----------------------------------------------------

    print("\nCompany Growth 2025 -> 2026:")
    print(
        calculate_yearly_growth(
            data,
            start_year=2025,
            end_year=2026
        )
    )

    # -----------------------------------------------------
    # SEGMENT
    # -----------------------------------------------------

    print("\nSegment Performance 2026:")
    print(
        calculate_segment_performance(
            data,
            year=2026
        )
    )

    print("\nHighest Revenue Segment 2026:")
    print(
        calculate_highest_segment_revenue(
            data,
            year=2026
        )
    )

    # -----------------------------------------------------
    # REGION
    # -----------------------------------------------------

    print("\nRegion Performance 2026:")
    print(
        calculate_region_performance(
            data,
            year=2026
        )
    )

    print("\nHighest Revenue Region 2026:")
    print(
        calculate_highest_region_revenue(
            data,
            year=2026
        )
    )

    # -----------------------------------------------------
    # APPLIANCE
    # -----------------------------------------------------

    print("\nAppliance Repair Performance 2026:")
    print(
        calculate_appliance_repair_performance(
            data,
            year=2026
        )
    )

    print("\nLowest Appliance Repair Margin 2026:")
    print(
        calculate_lowest_appliance_repair_margin(
            data,
            year=2026
        )
    )

    print("\nHighest Appliance Repair Margin 2026:")
    print(
        calculate_highest_appliance_repair_margin(
            data,
            year=2026
        )
    )

    # -----------------------------------------------------
    # WARRANTY
    # -----------------------------------------------------

    print("\nWarranty Performance 2026:")
    print(
        calculate_warranty_performance(
            data,
            year=2026
        )
    )

    # -----------------------------------------------------
    # MULTI-HOP
    # -----------------------------------------------------

    print("\nDeclining Customers With High Repair Costs:")
    print(
        calculate_declining_customers_high_repair_cost(
            data,
            start_year=2025,
            end_year=2026
        )
    )

    print("\n" + "=" * 70)
    print("CALCULATIONS TEST COMPLETE")
    print("=" * 70)