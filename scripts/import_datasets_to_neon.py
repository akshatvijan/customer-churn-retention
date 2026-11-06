
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not in .env")

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# CSV files and their PostgreSQL table names
DATASETS = {
    "data/raw/olist_customers_dataset.csv": "olist_customers",
    "data/raw/olist_geolocation_dataset.csv": "olist_geolocation",
    "data/raw/olist_orders_dataset.csv": "olist_orders",
    "data/raw/olist_order_items_dataset.csv": "olist_order_items",
    "data/raw/olist_order_payments_dataset.csv": "olist_order_payments",
    "data/raw/olist_order_reviews_dataset.csv": "olist_order_reviews",
    "data/raw/olist_products_dataset.csv": "olist_products",
    "data/raw/olist_sellers_dataset.csv": "olist_sellers",
    "data/raw/product_category_name_translation.csv": "product_category_translation",
    "data/raw/Telco-Customer-Churn.csv": "telco_customer_churn",
    "data/processed/olist_customer_features.csv": "olist_customer_features",
    "data/synthetic/synthetic_retention_scenarios.csv": "synthetic_retention_scenarios",
}

CHUNK_SIZE = 5000


def main():
    engine = create_engine(DATABASE_URL)

    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names(schema="public"))

        print(f"Datasets to process: {len(DATASETS)}")
        print(f"Existing public tables: {len(existing_tables)}")

        for relative_path, table_name in DATASETS.items():
            csv_path = BASE_DIR / relative_path

            print(f"\nProcessing: {csv_path.name}")
            print(f"Target table: {table_name}")

            if not csv_path.exists():
                print("SKIPPED: CSV file not found.")
                continue

            # Never replace or append to an existing target table.
            if table_name in existing_tables:
                print("SKIPPED: Target table already exists; no changes made.")
                continue

            # Read a small sample to identify columns.
            sample = pd.read_csv(csv_path, nrows=5)

            # Create the table from the first chunk, then append later chunks.
            first_chunk = True
            total_rows = 0

            for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE):
                chunk.to_sql(
                    name=table_name,
                    con=engine,
                    schema="public",
                    if_exists="fail" if first_chunk else "append",
                    index=False,
                    chunksize=1000,
                    method="multi",
                )

                total_rows += len(chunk)
                first_chunk = False

                print(f"Imported rows: {total_rows:,}", end="\r")

            # Handle an empty CSV with headers.
            if first_chunk:
                sample.head(0).to_sql(
                    name=table_name,
                    con=engine,
                    schema="public",
                    if_exists="fail",
                    index=False,
                )

            existing_tables.add(table_name)
            print(f"\nSUCCESS: {table_name} — {total_rows:,} rows imported.")

        print("\nDataset import process completed.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
