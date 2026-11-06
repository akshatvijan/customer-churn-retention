from mcp.server.fastmcp import FastMCP

from retention_intelligence.rag.retrieval import retrieve_knowledge
from retention_intelligence.services.milvus_service import (
    get_churn_collection_schema,
    get_churn_collection_status
)


mcp = FastMCP("retention-knowledge-server")


@mcp.tool()
def search_retention_knowledge(
    query: str,
    top_k: int = 5,
    category: str | None = None
) -> dict:
    """
    Search the existing Milvus knowledge base for
    customer retention and fulfilment-related knowledge.
    """

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    if top_k < 1 or top_k > 20:
        raise ValueError("top_k must be between 1 and 20")

    try:
        documents = retrieve_knowledge(
            query=query.strip(),
            top_k=top_k,
            category=category
        )

        return {
            "status": "success",
            "query": query,
            "total_results": len(documents),
            "results": documents
        }

    except Exception as error:
        raise RuntimeError(
            f"Retention knowledge search failed: {str(error)}"
        ) from error


@mcp.tool()
def get_knowledge_base_status() -> dict:
    """
    Get the existing Milvus knowledge collection status.
    """

    try:
        schema = get_churn_collection_schema()
        status = get_churn_collection_status()

        return {
            "status": "success",
            "collection_schema": schema,
            "collection_status": status
        }

    except Exception as error:
        raise RuntimeError(
            f"Knowledge base status retrieval failed: {str(error)}"
        ) from error


if __name__ == "__main__":
    mcp.run(transport="stdio")