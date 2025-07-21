"""
Database configuration and setup for Market Sector Sentiment Analysis Tool
Using PostgreSQL + TimescaleDB for production-ready time-series data
"""

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from pathlib import Path
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from core.config import get_settings

# Get settings
settings = get_settings()

# PostgreSQL Database Configuration
POSTGRES_USER = "market_user"
POSTGRES_PASSWORD = "market_password"
POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = "5433"
POSTGRES_DB = "market_sentiment"

# Build PostgreSQL connection URL (password required by client even with trust auth)
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create engine with PostgreSQL optimizations
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug if settings else False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_database():
    """Initialize PostgreSQL + TimescaleDB database"""
    print("Initializing PostgreSQL + TimescaleDB database...")

    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version_row = result.fetchone()
            version = version_row[0] if version_row else "Unknown"
            print(f"Connected to: {version}")

            # Check TimescaleDB
            result = conn.execute(
                text(
                    "SELECT default_version FROM pg_available_extensions WHERE name = 'timescaledb'"
                )
            )
            timescale_version = result.fetchone()
            if timescale_version:
                print(f"TimescaleDB available: {timescale_version[0]}")
            else:
                print("WARNING: TimescaleDB extension not found")

    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Make sure PostgreSQL is running: docker compose up -d postgres")
        raise

    # Import all models to register them
    from models import stock_universe, sector_sentiment, stock_data

    # Create all tables (schema already created by init.sql)
    Base.metadata.create_all(bind=engine)

    print(f"PostgreSQL database ready at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")


async def get_db_info():
    """Get database information for health checks"""
    try:
        with SessionLocal() as db:
            # Get table counts
            from models.stock_universe import StockUniverse
            from models.sector_sentiment import SectorSentiment

            # Basic counts
            stock_count = db.execute(
                text("SELECT COUNT(*) FROM stock_universe")
            ).scalar()
            sector_count = db.execute(
                text("SELECT COUNT(*) FROM sector_sentiment")
            ).scalar()

            # TimescaleDB specific info
            hypertable_info = db.execute(
                text(
                    """
                SELECT schemaname, tablename, num_chunks 
                FROM timescaledb_information.hypertables
            """
                )
            ).fetchall()

            return {
                "status": "healthy",
                "database_type": "PostgreSQL + TimescaleDB",
                "connection_url": f"postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
                "stock_count": stock_count,
                "sector_count": sector_count,
                "hypertables": [
                    {"schema": ht[0], "table": ht[1], "chunks": ht[2]}
                    for ht in hypertable_info
                ],
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_type": "PostgreSQL + TimescaleDB",
            "connection_url": f"postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        }


# Context manager for database sessions
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[Session, None]:
    """Async context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
