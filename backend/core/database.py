"""
Database configuration and setup for Market Sector Sentiment Analysis Tool
Using SQLite for development, with easy migration path to PostgreSQL/TimescaleDB
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from core.config import get_settings

# Get settings
settings = get_settings()

# Database URL
if settings.credentials and settings.credentials.database.sqlite_path:
    db_path = settings.credentials.database.sqlite_path
else:
    db_path = "./data/sentiment.db"

# Ensure data directory exists
Path(db_path).parent.mkdir(parents=True, exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///{db_path}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multiple threads (needed for FastAPI)
        "timeout": 30  # 30 second timeout
    },
    poolclass=StaticPool,
    echo=settings.debug if settings else False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_database():
    """Initialize database with tables"""
    print("Initializing SQLite database...")
    
    # Import all models to register them
    from models import stock_universe, sector_sentiment, stock_data
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print(f"Database initialized at {db_path}")
    
    # Run initial data seeding if needed
    await seed_initial_data()

async def seed_initial_data():
    """Seed initial data for development"""
    print("Seeding initial data...")
    
    # Import models
    from models.sector_sentiment import SectorSentiment
    from models.stock_universe import StockUniverse
    
    with SessionLocal() as db:
        # Check if we already have data
        existing_sectors = db.query(SectorSentiment).count()
        if existing_sectors > 0:
            print("Database already has data, skipping seed")
            return
        
        # Create initial sector entries
        sectors = [
            "technology", "healthcare", "energy", "financial",
            "consumer_discretionary", "industrials", "materials", "utilities"
        ]
        
        for sector in sectors:
            sector_record = SectorSentiment(
                sector=sector,
                sentiment_score=0.0,
                color_classification="blue_neutral",
                confidence_level=0.5,
                last_updated=None
            )
            db.add(sector_record)
        
        db.commit()
        print(f"Seeded {len(sectors)} sectors successfully")

async def get_db_info():
    """Get database information for health checks"""
    try:
        with SessionLocal() as db:
            # Get table counts
            from models.stock_universe import StockUniverse
            from models.sector_sentiment import SectorSentiment
            
            stock_count = db.query(StockUniverse).count()
            sector_count = db.query(SectorSentiment).count()
            
            return {
                "status": "healthy",
                "database_path": db_path,
                "stock_count": stock_count,
                "sector_count": sector_count,
                "engine_info": str(engine.url)
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_path": db_path
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