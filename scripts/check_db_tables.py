import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL .env file vich nahi mili.")

engine = create_engine(database_url, pool_pre_ping=True)

try:
    with engine.connect() as connection:
        print("\nConnected to Neon PostgreSQL successfully!")

        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="public")

        if not tables:
            print("\nPublic schema vich koi table nahi mili.")

        for table in tables:
            count = connection.execute(
                text(f'SELECT COUNT(*) FROM public."{table}"')
            ).scalar_one()

            print(f"{table}: {count:,} rows")

            columns = inspector.get_columns(table, schema="public")
            print("Columns:", ", ".join(column["name"] for column in columns))
            print("-" * 60)

except Exception as error:
    print(f"\nDatabase verification failed: {error}")

finally:
    engine.dispose()
