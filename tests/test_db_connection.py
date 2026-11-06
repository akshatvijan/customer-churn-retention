from sqlalchemy import text
from retention_intelligence.db.connection import engine

def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        assert result.scalar() == 1