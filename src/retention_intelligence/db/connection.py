import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env file")

# Normalize PostgreSQL driver for psycopg (v3) compatibility
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    try:
        import psycopg
        # If psycopg v3 is installed and psycopg2 is not present, use postgresql+psycopg
        try:
            import psycopg2
        except ImportError:
            prefix = "postgresql+psycopg://"
            DATABASE_URL = prefix + DATABASE_URL.split("://", 1)[1]
    except ImportError:
        pass

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()