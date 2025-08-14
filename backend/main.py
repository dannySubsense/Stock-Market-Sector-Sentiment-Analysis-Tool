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
from services.sma_30m_pipeline import get_sma_pipeline_30m
from services.intraday_ingestor import run_intraday_loop
from sqlalchemy import text
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
    intraday_stop: asyncio.Event | None = None
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
        # Seed 1D/30m at startup if missing or stale
        batch30, _ = freshness.get_latest_complete_batch(db, timeframe="30min")
        if not batch30:
            try:
                async def _seed_startup():
                    try:
                        # Always fetch→store→recompute 1D, then 30m, on first boot if stale/missing
                        from services.fmp_batch_data_service import FMPBatchDataService
                        from services.data_persistence_service import get_persistence_service
                        fmp = FMPBatchDataService()
                        persistence = get_persistence_service()
                        syms = [r[0] for r in db.execute(text("SELECT symbol FROM stock_universe WHERE is_active = true")).fetchall()]
                        quotes = await fmp.get_universe_price_data(syms)
                        payload = []
                        for q in quotes:
                            try:
                                changes_pct = getattr(q, "fmp_changes_percentage", None)
                                if changes_pct is None and (q.previous_close or 0) > 0:
                                    changes_pct = ((q.current_price - q.previous_close) / q.previous_close) * 100.0
                                payload.append({
                                    "symbol": q.symbol,
                                    "price": q.current_price,
                                    "previousClose": q.previous_close,
                                    "changesPercentage": float(changes_pct or 0.0),
                                    "volume": q.current_volume,
                                    "avgVolume": q.avg_20_day_volume,
                                    "open": q.current_price,
                                    "dayLow": q.current_price,
                                    "dayHigh": q.current_price,
                                    "marketCap": 0,
                                })
                            except Exception:
                                continue
                        if payload:
                            await persistence.store_fmp_batch_price_data(payload)
                        from services.sma_1d_pipeline import get_sma_pipeline_1d
                        sma1d = get_sma_pipeline_1d()
                        await sma1d.run()
                        sma30 = get_sma_pipeline_30m()
                        await sma30.run()
                        print("Seeded initial 1D and 30m batches at startup")
                    except Exception as e:
                        print(f"Startup seed failed: {e}")

                asyncio.create_task(_seed_startup())
            except Exception as e:
                print(f"Bootstrap 30m check failed: {e}")

        # Start intraday ingest loop if enabled
        if settings.enable_intraday_ingest:
            intraday_stop = asyncio.Event()
            asyncio.create_task(run_intraday_loop(intraday_stop))
    except Exception as e:
        print(f"Bootstrap 3D check failed: {e}")

    yield

    # Shutdown
    print("Shutting down Market Sector Sentiment Analysis Tool")
    try:
        if intraday_stop:
            intraday_stop.set()
    except Exception:
        pass


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
