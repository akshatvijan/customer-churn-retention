
import sys
from functools import lru_cache

from retention_intelligence.services.milvus_service import (
    get_milvus_client,
    COLLECTION_NAME
)


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

MILVUS_TIMEOUT = 15


def log(message: str) -> None:
    """Send debug logs to STDERR, keeping STDOUT clean for MCP."""
    print(message, file=sys.stderr, flush=True)


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model only once when required.
    """

    from sentence_transformers import SentenceTransformer

    log("[RAG] Loading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu"
    )

    log("[RAG] Embedding model loaded.")

    return model


def retrieve_knowledge(
    query: str,
    top_k: int = 3,
    category: str | None = None
) -> list[dict]:

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty")

    if not isinstance(top_k, int) or not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    if category is not None:
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category must be a non-empty string")

        if '"' in category or "\\" in category:
            raise ValueError("Invalid category filter")

    log("[RAG] Generating query embedding...")

    model = get_embedding_model()

    query_embedding = model.encode(
        query.strip(),
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    client = get_milvus_client()

    try:
        search_filter = (
            f'category == "{category}"'
            if category
            else ""
        )

        log("[RAG] Searching Milvus...")

        results = client.search(
            collection_name=COLLECTION_NAME,
            data=[query_embedding.tolist()],
            anns_field="embedding",
            filter=search_filter,
            limit=top_k,
            output_fields=[
                "text",
                "category",
                "source",
                "metadata"
            ],
            search_params={
                "metric_type": "COSINE",
                "params": {}
            },
            timeout=MILVUS_TIMEOUT
        )

        documents = []

        if results:
            for result in results[0]:
                entity = result.get("entity", {})

                documents.append({
                    "text": entity.get("text"),
                    "category": entity.get("category"),
                    "source": entity.get("source"),
                    "metadata": entity.get("metadata", {}),
                    "similarity_score": float(
                        result.get("distance", 0)
                    )
                })

        log(f"[RAG] Retrieved {len(documents)} documents.")

        return documents

    finally:
        client.close()
