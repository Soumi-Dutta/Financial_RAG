import json
import re
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_STORE_PATH = PROJECT_ROOT / "data" / "vector_store"

INDEX_PATH = VECTOR_STORE_PATH / "financial_rag.index"
METADATA_PATH = VECTOR_STORE_PATH / "metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"


def load_vector_store():
    index = faiss.read_index(str(INDEX_PATH))

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        documents = json.load(file)

    model = SentenceTransformer(MODEL_NAME)

    return index, documents, model


def search(query, top_k=5):
    index, documents, model = load_vector_store()

    # -------------------------------------------------
    # Detect an explicitly mentioned customer ID
    # Example: "Tell me about customer C0062"
    # -------------------------------------------------

    customer_match = re.search(
        r"\bC\d{4}\b",
        query.upper()
    )

    customer_id = customer_match.group(0) if customer_match else None

    # -------------------------------------------------
    # If a customer ID is explicitly mentioned,
    # search only that customer's documents.
    # -------------------------------------------------

    if customer_id:

        matching_documents = []

        for document in documents:
            metadata = document["metadata"]

            if metadata.get("customer_id") == customer_id:
                matching_documents.append(document)

        # If we found matching customer records,
        # calculate similarity only against those records.
        if matching_documents:

            texts = [
                document["text"]
                for document in matching_documents
            ]

            embeddings = model.encode(
                texts,
                convert_to_numpy=True
            ).astype("float32")

            query_embedding = model.encode(
                [query],
                convert_to_numpy=True
            ).astype("float32")

            temp_index = faiss.IndexFlatL2(
                embeddings.shape[1]
            )

            temp_index.add(embeddings)

            distances, indices = temp_index.search(
                query_embedding,
                min(top_k, len(matching_documents))
            )

            results = []

            for distance, index_position in zip(
                distances[0],
                indices[0]
            ):
                document = matching_documents[index_position]

                results.append(
                    {
                        "text": document["text"],
                        "metadata": document["metadata"],
                        "distance": float(distance),
                    }
                )

            return results

    # -------------------------------------------------
    # Normal semantic search
    # -------------------------------------------------

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for distance, index_position in zip(
        distances[0],
        indices[0]
    ):

        if index_position == -1:
            continue

        document = documents[index_position]

        results.append(
            {
                "text": document["text"],
                "metadata": document["metadata"],
                "distance": float(distance),
            }
        )

    return results


if __name__ == "__main__":

    query = input("\nEnter your search question: ")

    results = search(query, top_k=5)

    print("\n--- Search Results ---")

    for number, result in enumerate(
        results,
        start=1
    ):

        print(f"\nResult {number}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Source: {result['metadata']['source']}")
        print(result["text"])