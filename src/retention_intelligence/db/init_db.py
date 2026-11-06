
from retention_intelligence.db.connection import engine, Base

from retention_intelligence.db.model import (
    TelcoChurnPrediction,
    OlistRetentionRisk,
    RetentionRecommendation,
    RetentionAuditLog
)


def create_tables():

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")

    print("Available tables:")

    for table_name in Base.metadata.tables:
        print(f"- {table_name}")


if __name__ == "__main__":
    create_tables()
