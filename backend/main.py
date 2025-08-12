"""
Market Sector Sentiment Analysis Tool - Main FastAPI Application
Slice 1A: Foundation Implementation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path

# Import core modules (will be created)
from core.config import get_settings
from core.database import init_database, get_db
from services.data_freshness_service import get_freshness_service
from api.routes.sectors import get_sma_pipeline_3d
import asyncio
from api.routes import health, sectors, stocks, analysis, cache

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting Market Sector Sentiment Analysis Tool")
    await init_database()
    print("Database initialized")

    # Bootstrap: if no 3D batch exists, enqueue one recompute once at startup
    try:
        freshness = get_freshness_service()
        # Use a short-lived session to check for existing 3D data
        db = next(get_db())
        batch, _ = freshness.get_latest_complete_batch(db, timeframe="3day")
        if not batch:
            async def _seed_3d():
                try:
                    sma3d = get_sma_pipeline_3d()
                    await sma3d.run()
                    print("Seeded initial 3D batch at startup")
                except Exception as e:
                    print(f"Failed to seed 3D batch at startup: {e}")

            asyncio.create_task(_seed_3d())
    except Exception as e:
        print(f"Bootstrap 3D check failed: {e}")

    yield

    # Shutdown
    print("Shutting down Market Sector Sentiment Analysis Tool")


# Create FastAPI app
app = FastAPI(
    title="Market Sector Sentiment Analysis Tool",
    description="AI-powered sector-first sentiment analysis platform for small-cap traders",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(sectors.router, prefix="/api", tags=["sectors"])
app.include_router(stocks.router, prefix="/api", tags=["stocks"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(cache.router, prefix="/api", tags=["cache"])


@app.get("/")
async def root():
    """Root endpoint with basic system info"""
    return {
        "message": "Market Sector Sentiment Analysis Tool API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
