import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS_PATH = PROJECT_ROOT / "data" / "rag_documents.json"
VECTOR_STORE_PATH = PROJECT_ROOT / "data" / "vector_store"

INDEX_PATH = VECTOR_STORE_PATH / "financial_rag.index"
METADATA_PATH = VECTOR_STORE_PATH / "metadata.json"


# Local embedding model
MODEL_NAME = "all-MiniLM-L6-v2"


def load_documents():
    """Load the RAG documents created during indexing."""

    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as file:
        documents = json.load(file)

    print(f"Loaded {len(documents)} documents.")

    return documents


def create_vector_store():
    """Create embeddings and save them in a FAISS vector index."""

    documents = load_documents()

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [document["text"] for document in documents]

    print("Creating embeddings...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype("float32")

    print(f"Embedding shape: {embeddings.shape}")

    # Create FAISS index
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    # Create output directory
    VECTOR_STORE_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save FAISS index
    faiss.write_index(
        index,
        str(INDEX_PATH)
    )

    # Save documents/metadata alongside the index
    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\nVector store created successfully!")
    print(f"Documents indexed: {index.ntotal}")
    print(f"Index saved to: {INDEX_PATH}")
    print(f"Metadata saved to: {METADATA_PATH}")


if __name__ == "__main__":
    create_vector_store()