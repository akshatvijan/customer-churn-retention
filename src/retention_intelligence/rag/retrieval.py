
from sentence_transformers import SentenceTransformer

from retention_intelligence.services.milvus_service import (
    get_milvus_client,
    COLLECTION_NAME
)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

embedding_model = None


def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        embedding_model = SentenceTransformer(MODEL_NAME)

    return embedding_model


def retrieve_knowledge(
    query: str,
    top_k: int = 3,
    category: str | None = None
) -> list[dict]:

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    model = get_embedding_model()

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    client = get_milvus_client()

    try:
        search_filter = (
            f'category == "{category}"'
            if category
            else ""
        )

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
            }
        )

        documents = []

        for result in results[0]:
            entity = result.get("entity", {})

            documents.append({
                "text": entity.get("text"),
                "category": entity.get("category"),
                "source": entity.get("source"),
                "metadata": entity.get("metadata", {}),
                "similarity_score": float(result.get("distance", 0))
            })

        return documents

    finally:
        client.close()
