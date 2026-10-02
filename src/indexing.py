import json
from pathlib import Path

from ingestion import load_data
from preprocessing import clean_data


OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "rag_documents.json"
)


def create_customer_documents(data):
    """
    Convert customer-year financial records into searchable RAG documents.
    """

    df = data["Customer_Year_Summary"]

    documents = []

    for _, row in df.iterrows():

        text = (
            f"Customer {row['Customer_ID']} is a "
            f"{row['Customer_Type']} in the "
            f"{row['Business_Segment']} segment and "
            f"{row['Region']} region. "
            f"For {int(row['Year'])}, the customer generated "
            f"revenue of ₹{row['Revenue_INR']:,.2f}, "
            f"direct cost of ₹{row['Direct_Cost_INR']:,.2f}, "
            f"gross profit of ₹{row['Gross_Profit_INR']:,.2f}, "
            f"with {int(row['Service_Count'])} services. "
            f"Warranty revenue was "
            f"₹{row['Warranty_Revenue_INR']:,.2f}, "
            f"and gross margin was "
            f"{row['Gross_Margin_Pct']:.2f}%."
        )

        metadata = {
            "source": "Customer_Year_Summary",
            "customer_id": row["Customer_ID"],
            "customer_type": row["Customer_Type"],
            "business_segment": row["Business_Segment"],
            "region": row["Region"],
            "year": int(row["Year"]),
        }

        documents.append({
            "text": text,
            "metadata": metadata
        })

    return documents


def create_repair_documents(data):
    """
    Convert repair transactions into searchable RAG documents.
    """

    df = data["Service_Transactions"]

    df = df[df["Service_Type"] == "Breakdown Repair"]

    documents = []

    for _, row in df.iterrows():

        text = (
            f"Service {row['Service_ID']} was a breakdown repair "
            f"for customer {row['Customer_ID']} in {int(row['Year'])}. "
            f"The appliance type was {row['Appliance_Type']} "
            f"in the {row['Region']} region. "
            f"Total revenue was ₹{row['Total_Revenue_INR']:,.2f}, "
            f"direct cost was ₹{row['Direct_Cost_INR']:,.2f}, "
            f"and gross profit was ₹{row['Gross_Profit_INR']:,.2f}. "
            f"Under warranty: {row['Under_Warranty']}."
        )

        metadata = {
            "source": "Service_Transactions",
            "service_id": row["Service_ID"],
            "customer_id": row["Customer_ID"],
            "year": int(row["Year"]),
            "region": row["Region"],
            "appliance_type": row["Appliance_Type"],
            "service_type": row["Service_Type"],
            "under_warranty": row["Under_Warranty"],
        }

        documents.append({
            "text": text,
            "metadata": metadata
        })

    return documents


def create_documents():
    """
    Create all searchable RAG documents.
    """

    sheets = load_data()
    data = clean_data(sheets)

    documents = []

    documents.extend(create_customer_documents(data))
    documents.extend(create_repair_documents(data))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nCreated {len(documents)} RAG documents.")
    print(f"Saved to: {OUTPUT_PATH}")

    return documents


if __name__ == "__main__":
    create_documents()