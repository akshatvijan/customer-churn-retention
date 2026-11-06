
import os

from dotenv import load_dotenv
from pymilvus import MilvusClient


load_dotenv()

COLLECTION_NAME = "customer_churn_knowledge"


def get_milvus_client():

    uri = os.getenv("MILVUS_URI")
    token = os.getenv("MILVUS_TOKEN")

    if not uri:
        raise ValueError("MILVUS_URI is missing from .env")

    if not token:
        raise ValueError("MILVUS_TOKEN is missing from .env")

    try:
        client = MilvusClient(
            uri=uri,
            token=token
        )

        return client

    except Exception as error:
        raise ConnectionError(
            f"Milvus connection failed: {str(error)}"
        ) from error


def get_churn_collection_schema():

    client = get_milvus_client()

    try:
        return client.describe_collection(
            collection_name=COLLECTION_NAME
        )

    finally:
        client.close()


def get_churn_knowledge_samples(limit: int = 10):

    client = get_milvus_client()

    try:
        return client.query(
            collection_name=COLLECTION_NAME,
            filter="id >= 0",
            output_fields=[
                "text",
                "category",
                "source",
                "metadata"
            ],
            limit=limit
        )

    finally:
        client.close()


def get_churn_collection_status():

    client = get_milvus_client()

    try:
        stats = client.get_collection_stats(
            collection_name=COLLECTION_NAME
        )

        indexes = client.list_indexes(
            collection_name=COLLECTION_NAME
        )

        return {
            "collection_name": COLLECTION_NAME,
            "collection_stats": stats,
            "indexes": indexes
        }

    finally:
        client.close()


def get_churn_vector_index():

    client = get_milvus_client()

    try:
        return client.describe_index(
            collection_name=COLLECTION_NAME,
            index_name="embedding"
        )

    finally:
        client.close()


if __name__ == "__main__":

    print("\n1. COLLECTION SCHEMA")
    print(get_churn_collection_schema())

    print("\n2. COLLECTION STATUS")
    print(get_churn_collection_status())

    print("\n3. VECTOR INDEX DETAILS")
    print(get_churn_vector_index())

    print("\n4. KNOWLEDGE SAMPLES")

    samples = get_churn_knowledge_samples()

    for sample in samples:
        print({
            "text": sample["text"],
            "category": sample["category"],
            "source": sample["source"]
        })

    print(f"\nTotal knowledge records retrieved: {len(samples)}")
