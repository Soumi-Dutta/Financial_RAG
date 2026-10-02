import pandas as pd
from pathlib import Path


# Location of our Excel dataset
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "financial_rag_poc_dataset.xlsx"


def load_data():
    """Load all sheets from the financial Excel dataset."""
    sheets = pd.read_excel(DATA_PATH, sheet_name=None)

    print("Dataset loaded successfully!")
    print("\nAvailable sheets:")

    for sheet_name, dataframe in sheets.items():
        print(f"- {sheet_name}: {len(dataframe)} rows")

    return sheets


if __name__ == "__main__":
    load_data()