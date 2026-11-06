
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from retention_intelligence.services.milvus_service import (
    get_milvus_client
)


BASE_DIR = Path(__file__).resolve().parents[3]

COLLECTION_NAME = "customer_churn_knowledge"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

KNOWLEDGE_FILES = {
    "fulfilment": {
        "path": (
            BASE_DIR
            / "data"
            / "knowledge"
            / "fulfilment"
            / "fulfilment_knowledge.json"
        ),
        "duplicate_check_category": "inactivity"
    },
    "retention": {
        "path": (
            BASE_DIR
            / "data"
            / "knowledge"
            / "retention"
            / "retention_knowledge.json"
        ),
        "duplicate_check_category": "retention_strategy"
    }
}


def load_knowledge(file_path: Path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Knowledge file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        documents = json.load(file)

    if not documents:
        raise ValueError("Knowledge file is empty")

    for document in documents:

        for field in ("text", "category", "source"):

            if not document.get(field):
                raise ValueError(
                    f"Missing '{field}' in a knowledge document"
                )

    return documents


def ingest_knowledge(knowledge_type: str):

    if knowledge_type not in KNOWLEDGE_FILES:
        raise ValueError(
            f"Unsupported knowledge type: {knowledge_type}"
        )

    config = KNOWLEDGE_FILES[knowledge_type]

    client = get_milvus_client()

    try:

        # Check whether this knowledge category already exists
        existing = client.query(
            collection_name=COLLECTION_NAME,
            filter=(
                f'category == "{config["duplicate_check_category"]}"'
            ),
            output_fields=["id"],
            limit=1
        )

        if existing:
            raise RuntimeError(
                f"{knowledge_type.capitalize()} knowledge may "
                "already be ingested. Check existing records "
                "before retrying."
            )

        # Load knowledge documents
        documents = load_knowledge(config["path"])

        texts = [
            document["text"]
            for document in documents
        ]

        # Generate Hugging Face embeddings
        embedding_model = SentenceTransformer(MODEL_NAME)

        embeddings = embedding_model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        if embeddings.shape[1] != 384:
            raise ValueError(
                f"Expected 384 dimensions, got {embeddings.shape[1]}"
            )

        records = []

        for document, embedding in zip(documents, embeddings):

            records.append({
                "text": document["text"],
                "embedding": embedding.tolist(),
                "category": document["category"],
                "source": document["source"],
                "metadata": document.get("metadata", {})
            })

        # Insert into existing collection
        result = client.insert(
            collection_name=COLLECTION_NAME,
            data=records
        )

        client.flush(
            collection_name=COLLECTION_NAME
        )

        print(
            f"{knowledge_type.capitalize()} knowledge ingestion completed."
        )

        print(f"Inserted records: {result.get('insert_count')}")
        print(f"Embedding dimensions: {embeddings.shape[1]}")
        print(f"Collection: {COLLECTION_NAME}")

    finally:
        client.close()


def ingest_fulfilment_knowledge():

    ingest_knowledge("fulfilment")


def ingest_retention_knowledge():

    ingest_knowledge("retention")


if __name__ == "__main__":

    # Run only the new retention ingestion
    ingest_retention_knowledge()
