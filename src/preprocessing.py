import pandas as pd


def clean_data(sheets):
    """Clean and standardize the important financial tables."""

    # Make copies so the original loaded data is not changed
    cleaned = {
        name: dataframe.copy()
        for name, dataframe in sheets.items()
    }

    # Clean column names
    for name, dataframe in cleaned.items():
        dataframe.columns = (
            dataframe.columns
            .astype(str)
            .str.strip()
            .str.replace(" ", "_")
        )

    # Convert Year columns to numeric where they exist
    for dataframe in cleaned.values():
        if "Year" in dataframe.columns:
            dataframe["Year"] = pd.to_numeric(
                dataframe["Year"],
                errors="coerce"
            )

    # Make financial numeric columns numeric
    financial_columns = [
        "Total_Revenue_INR",
        "Direct_Cost_INR",
        "Gross_Profit_INR",
        "Revenue_INR",
        "Cost_INR",
        "Profit_INR",
        "Warranty_Revenue_INR",
    ]

    for dataframe in cleaned.values():
        for column in financial_columns:
            if column in dataframe.columns:
                dataframe[column] = pd.to_numeric(
                    dataframe[column],
                    errors="coerce"
                )

    print("Data preprocessing completed!")

    return cleaned


if __name__ == "__main__":
    from ingestion import load_data

    sheets = load_data()
    cleaned_data = clean_data(sheets)

    print("\nCleaned sheets:")
    for name, dataframe in cleaned_data.items():
        print(f"- {name}: {len(dataframe)} rows")