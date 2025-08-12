"""
Sectors API Routes
Separate endpoints per timeframe for optimal performance and caching
Updated to use atomic batch operations with staleness detection
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from core.database import get_db
from core.config import get_settings
from services.data_freshness_service import get_freshness_service, DataFreshnessService
from services.sector_data_service import SectorDataService
from services.sector_filters import SectorFilters
from services.simple_sector_calculator import SectorCalculator
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
from services.fmp_batch_data_service import FMPBatchDataService
from services.sma_1d_pipeline import get_sma_pipeline_1d
from services.sma_3d_pipeline import get_sma_pipeline_3d
from services.sma_1w_pipeline import get_sma_pipeline_1w
from services.time_utils import utc_to_et_fields
import asyncio

router = APIRouter(prefix="/sectors", tags=["sectors"])
logger = logging.getLogger(__name__)
settings = get_settings()


# Lightweight in-process cache for 3day preview responses to keep UI toggling snappy
_preview_cache_3d: Dict[str, Dict[str, Any]] = {}
_preview_cache_3d_expiry: Dict[str, datetime] = {}

@router.get("/1day/", response_model=Dict[str, Any])
async def get_all_sectors_1day(
    include_stale: bool = True,
    calc: str | None = None,
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get all sector sentiment data for 1day timeframe
    Returns all 11 sectors with unified staleness flag for UI gray card display
    """
    try:
        # Preview recompute without persistence if calc is requested
        if calc in {"simple", "weighted"}:
            # Short-lived cache (e.g., 15s) to avoid recomputing on quick toggles
            cache_key = f"3day:{calc}"
            now_ts = datetime.now(timezone.utc)
            exp = _preview_cache_3d_expiry.get(cache_key)
            if exp and exp > now_ts:
                cached = _preview_cache_3d.get(cache_key)
                if cached:
                    return cached

            data_service = SectorDataService()
            filters = SectorFilters()
            calculator = SectorCalculator(mode=calc)
            rows = db.execute(text("SELECT DISTINCT sector FROM stock_universe WHERE is_active = true ORDER BY sector")).fetchall()
            sectors_dynamic = [r[0] for r in rows]

            def color_from_norm(n: float) -> str:
                if n <= -0.01:
                    return "dark_red"
                if n <= -0.003:
                    return "light_red"
                if n < 0.003:
                    return "blue_neutral"
                if n < 0.01:
                    return "light_green"
                return "dark_green"

            out: List[Dict[str, Any]] = []
            for s in sectors_dynamic:
                stocks = await data_service.get_filtered_sector_data(s, filters)
                perf = calculator.calculate_sector_performance(stocks)
                norm = round((perf or 0.0) / 100.0, 6)
                out.append({
                    "sector": s,
                    "timeframe": "1d",
                    "timestamp": now_ts.isoformat(),
                    "batch_id": "preview",
                    "sentiment_score": perf,
                    "sentiment_normalized": norm,
                    "color_classification": color_from_norm(norm),
                    "trading_signal": ("bullish" if norm >= 0.01 else ("bearish" if norm <= -0.01 else "neutral")),
                    "stock_count": len(stocks),
                    "created_at": now_ts.isoformat(),
                })

            return {
                "sectors": out,
                "metadata": {
                    "batch_id": "preview",
                    "timestamp": now_ts.isoformat(),
                    "timeframe": "1day",
                    "is_stale": False,
                    "staleness_threshold_hours": 1,
                    "age_minutes": 0.0,
                    "sector_count": len(out),
                    "integrity_valid": True,
                    "integrity_issues": [],
                    "preview": True,
                    "calc": calc,
                },
            }

        # Get latest complete batch for 1day timeframe
        batch_records, is_stale = freshness_service.get_latest_complete_batch(
            db, timeframe="1day"
        )

        if not batch_records:
            raise HTTPException(
                status_code=404,
                detail="No complete sector sentiment batches found for 1day timeframe",
            )

        # If caller doesn't want stale data and we only have stale data
        if not include_stale and is_stale:
            raise HTTPException(
                status_code=410,
                detail="Latest 1day data is stale. Refresh analysis recommended.",
            )

        # Validate batch integrity
        integrity = freshness_service.validate_batch_integrity(batch_records)
        if not integrity["valid"]:
            logger.warning(f"Batch integrity issues for 1day: {integrity['issues']}")

        # Convert to response format
        sectors = [record.to_dict() for record in batch_records]

        # Get batch age information
        batch_age = freshness_service.get_batch_age_info(batch_records[0].timestamp)

        et_meta = utc_to_et_fields(batch_records[0].timestamp)
        response = {
            "sectors": sectors,
            "metadata": {
                "batch_id": batch_records[0].batch_id,
                "timestamp": batch_records[0].timestamp.isoformat(),
                "timeframe": "1day",
                "is_stale": is_stale,
                "staleness_threshold_hours": 1,
                "age_minutes": batch_age["age_minutes"],
                "sector_count": len(batch_records),
                "integrity_valid": integrity["valid"],
                "integrity_issues": integrity.get("issues", []),
                **et_meta,
            },
        }

        if is_stale:
            response["warning"] = (
                "Data is stale for 1day timeframe. Consider refreshing analysis."
            )

        logger.info(
            f"Served {len(sectors)} sectors for 1day timeframe "
            f"from batch {batch_records[0].batch_id} (stale: {is_stale})"
        )
        # Optional: echo calc mode for UI/debug (actual calc used at write time)
        if calc:
            response["calc"] = calc
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all sectors for 1day: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/1week/", response_model=Dict[str, Any])
async def get_all_sectors_1week(
    include_stale: bool = True,
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get all sector sentiment data for 1week timeframe (persisted batch)
    """
    try:
        batch_records, is_stale = freshness_service.get_latest_complete_batch(
            db, timeframe="1week"
        )

        if not batch_records:
            raise HTTPException(
                status_code=404,
                detail="No complete sector sentiment batches found for 1week timeframe",
            )

        if not include_stale and is_stale:
            raise HTTPException(
                status_code=410,
                detail="Latest 1week data is stale. Refresh analysis recommended.",
            )

        integrity = freshness_service.validate_batch_integrity(batch_records)
        sectors = [record.to_dict() for record in batch_records]
        batch_age = freshness_service.get_batch_age_info(
            batch_records[0].timestamp, timeframe="1week"
        )
        et_meta = utc_to_et_fields(batch_records[0].timestamp)
        response = {
            "sectors": sectors,
            "metadata": {
                "batch_id": batch_records[0].batch_id,
                "timestamp": batch_records[0].timestamp.isoformat(),
                "timeframe": "1week",
                "is_stale": is_stale,
                "staleness_threshold_hours": 72,
                "age_minutes": batch_age["age_minutes"],
                "sector_count": len(batch_records),
                "integrity_valid": integrity["valid"],
                "integrity_issues": integrity.get("issues", []),
                **et_meta,
            },
        }
        if is_stale:
            response["warning"] = (
                "Data is stale for 1week timeframe. Consider refreshing analysis."
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all sectors for 1week: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/1week/recompute", status_code=status.HTTP_403_FORBIDDEN)
async def recompute_1week_blocked():
    """UI does not support 1week recompute; ops can enable later with force semantics."""
    return {"status": "blocked", "message": "1week recompute is disabled from API"}

@router.get("/1day/debug/sector-inputs", response_model=Dict[str, Any])
async def debug_sector_inputs_1day(
    sector: str,
    db: Session = Depends(get_db),
):
    """
    Debug-only: Inspect latest-per-symbol inputs for a sector (1D).
    Reports counts and preview simple/weighted means from raw latest quotes.
    Does NOT persist anything.
    """
    try:
        # Latest row per symbol in sector
        rows = db.execute(
            text(
                """
                WITH latest AS (
                  SELECT sp.symbol,
                         sp.price,
                         sp.previous_close,
                         sp.changes_percentage,
                         sp.volume,
                         ROW_NUMBER() OVER (
                           PARTITION BY sp.symbol
                           ORDER BY sp.fmp_timestamp DESC, sp.recorded_at DESC
                         ) AS rn
                  FROM stock_prices_1d sp
                  JOIN stock_universe su ON sp.symbol = su.symbol
                  WHERE su.sector = :sector AND su.is_active = true
                )
                SELECT symbol, price, previous_close, changes_percentage, volume
                FROM latest WHERE rn = 1
                """
            ),
            {"sector": sector},
        ).fetchall()

        total = len(rows)
        non_null_cp = 0
        prev_close_ok = 0
        simple_vals_cp: list[float] = []
        simple_vals_derived: list[float] = []
        weighted_input: list[Dict[str, Any]] = []

        for sym, price, prev_close, cp, vol in rows:
            price_f = float(price or 0.0)
            prev_f = float(prev_close or 0.0)
            vol_i = int(vol or 0)
            if cp is not None:
                non_null_cp += 1
                try:
                    simple_vals_cp.append(float(cp))
                except Exception:
                    pass
            if prev_f > 0 and price_f > 0:
                prev_close_ok += 1
                ret = ((price_f - prev_f) / prev_f) * 100.0
                simple_vals_derived.append(ret)
                weighted_input.append({
                    "symbol": str(sym),
                    "changes_percentage": float(cp) if cp is not None else ret,
                    "current_price": price_f,
                    "volume": vol_i,
                })

        # Compute preview stats
        def _mean(vals: list[float]) -> float:
            return round(sum(vals) / len(vals), 4) if vals else 0.0

        from services.simple_sector_calculator import SectorCalculator
        calc_w = SectorCalculator(mode="weighted")
        weighted_preview = calc_w.calculate_sector_performance(weighted_input)

        return {
            "sector": sector,
            "counts": {
                "latest_symbols": total,
                "with_changes_percentage": non_null_cp,
                "with_valid_prev_close": prev_close_ok,
            },
            "preview": {
                "simple_from_changes_percentage": _mean(simple_vals_cp),
                "simple_with_derivation": _mean(simple_vals_derived),
                "weighted_with_derivation": weighted_preview,
            },
        }

    except Exception as e:
        logger.error(f"Debug sector inputs failed for {sector}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/3day/", response_model=Dict[str, Any])
async def get_all_sectors_3day(
    include_stale: bool = True,
    calc: str | None = None,
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get all sector sentiment data for 3day timeframe (persisted batch)
    """
    try:
        # Preview recompute without persistence if calc is requested (simple/weighted)
        if calc in {"simple", "weighted"}:
            data_service = SectorDataService()
            filters = SectorFilters()
            calculator = SectorCalculator(mode=calc)
            rows = db.execute(text("SELECT DISTINCT sector FROM stock_universe WHERE is_active = true ORDER BY sector")).fetchall()
            sectors_dynamic = [r[0] for r in rows]
            now_ts = datetime.now(timezone.utc)

            def color_from_norm(n: float) -> str:
                if n <= -0.01:
                    return "dark_red"
                if n <= -0.003:
                    return "light_red"
                if n < 0.003:
                    return "blue_neutral"
                if n < 0.01:
                    return "light_green"
                return "dark_green"

            out: List[Dict[str, Any]] = []
            for sct in sectors_dynamic:
                stocks = await data_service.get_filtered_sector_data(sct, filters)
                # Fetch last-3 closes for all sector symbols in one SQL using window functions
                price_rows = db.execute(
                    text(
                        """
                        WITH sp AS (
                          SELECT symbol, price, recorded_at,
                                 ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY recorded_at DESC) AS rn
                          FROM stock_prices_1d
                          WHERE symbol IN (
                            SELECT symbol FROM stock_universe WHERE sector = :sector AND is_active = true
                          )
                        )
                        SELECT symbol,
                               MAX(price) FILTER (WHERE rn = 1) AS latest,
                               MAX(price) FILTER (WHERE rn = 3) AS prior
                        FROM sp
                        GROUP BY symbol
                        """
                    ),
                    {"sector": sct},
                ).fetchall()

                latest_prior: Dict[str, Dict[str, float]] = {}
                for sym, latest, prior in price_rows:
                    latest_prior[str(sym)] = {
                        "latest": float(latest or 0.0),
                        "prior": float(prior or 0.0),
                    }

                # Build synthetic stock list with 3D returns as changes_percentage
                preview_stocks: List[Dict[str, Any]] = []
                for st in stocks:
                    symbol = st.get("symbol")
                    if not symbol:
                        continue
                    lp = latest_prior.get(str(symbol))
                    if not lp:
                        continue
                    latest_v, prior_v = lp.get("latest", 0.0), lp.get("prior", 0.0)
                    if latest_v > 0 and prior_v > 0:
                        ret_pct = ((latest_v - prior_v) / prior_v) * 100.0
                        preview_stocks.append({
                            "symbol": symbol,
                            "changes_percentage": ret_pct,
                            "current_price": st.get("current_price") or st.get("price") or latest_v,
                            "volume": st.get("volume") or 0,
                        })

                perf = calculator.calculate_sector_performance(preview_stocks)
                norm = round((perf or 0.0) / 100.0, 6)
                out.append({
                    "sector": sct,
                    "timeframe": "3d",
                    "timestamp": now_ts.isoformat(),
                    "batch_id": "preview",
                    "sentiment_score": perf,
                    "sentiment_normalized": norm,
                    "color_classification": color_from_norm(norm),
                    "trading_signal": ("bullish" if norm >= 0.01 else ("bearish" if norm <= -0.01 else "neutral")),
                    "stock_count": len(preview_stocks),
                    "created_at": now_ts.isoformat(),
                })

            response_payload = {
                "sectors": out,
                "metadata": {
                    "batch_id": "preview",
                    "timestamp": now_ts.isoformat(),
                    "timeframe": "3day",
                    "is_stale": False,
                    "staleness_threshold_hours": 24,
                    "age_minutes": 0.0,
                    "sector_count": len(out),
                    "integrity_valid": True,
                    "integrity_issues": [],
                    "preview": True,
                    "calc": calc,
                },
            }

            # Cache for 15 seconds
            _preview_cache_3d[cache_key] = response_payload
            _preview_cache_3d_expiry[cache_key] = now_ts + timedelta(seconds=15)
            return response_payload

        batch_records, is_stale = freshness_service.get_latest_complete_batch(
            db, timeframe="3day"
        )

        if not batch_records:
            raise HTTPException(
                status_code=404,
                detail="No complete sector sentiment batches found for 3day timeframe",
            )

        if not include_stale and is_stale:
            raise HTTPException(
                status_code=410,
                detail="Latest 3day data is stale. Refresh analysis recommended.",
            )

        integrity = freshness_service.validate_batch_integrity(batch_records)

        sectors = [record.to_dict() for record in batch_records]

        batch_age = freshness_service.get_batch_age_info(
            batch_records[0].timestamp, timeframe="3day"
        )

        et_meta = utc_to_et_fields(batch_records[0].timestamp)
        response = {
            "sectors": sectors,
            "metadata": {
                "batch_id": batch_records[0].batch_id,
                "timestamp": batch_records[0].timestamp.isoformat(),
                "timeframe": "3day",
                "is_stale": is_stale,
                "staleness_threshold_hours": 24,
                "age_minutes": batch_age["age_minutes"],
                "sector_count": len(batch_records),
                "integrity_valid": integrity["valid"],
                "integrity_issues": integrity.get("issues", []),
                **et_meta,
            },
        }

        if is_stale:
            response["warning"] = (
                "Data is stale for 3day timeframe. Consider refreshing analysis."
            )

        logger.info(
            f"Served {len(sectors)} sectors for 3day timeframe "
            f"from batch {batch_records[0].batch_id} (stale: {is_stale})"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all sectors for 3day: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


_recompute_lock_3d = asyncio.Lock()


@router.post("/3day/recompute", status_code=status.HTTP_202_ACCEPTED)
async def recompute_3day(
    request: Request,
    background_tasks: BackgroundTasks,  # kept for signature stability; not used
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Secure recompute endpoint for 3day pipeline.
    - Requires settings.enable_recompute_api = True
    - Requires X-Admin-Token header if settings.admin_recompute_token is set
    - Enforces cooldown via settings.recompute_cooldown_seconds (initially shared)
    """
    try:
        if not settings.enable_recompute_api:
            raise HTTPException(status_code=403, detail="Recompute API disabled")

        token = request.headers.get("X-Admin-Token")
        if settings.admin_recompute_token and token != settings.admin_recompute_token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Cooldown check against latest 3day batch
        last_batch, _ = freshness_service.get_latest_complete_batch(db, timeframe="3day")
        if last_batch:
            last_ts = last_batch[0].timestamp
            age = freshness_service.get_batch_age_info(last_ts, timeframe="3day")
            if (age.get("age_minutes", 0) or 0) * 60 < settings.recompute_cooldown_seconds:
                raise HTTPException(status_code=429, detail="Recompute cooldown active")

        if _recompute_lock_3d.locked():
            raise HTTPException(status_code=409, detail="Another recompute is in progress")

        async def _do_recompute_3d():
            async with _recompute_lock_3d:
                sma3d = get_sma_pipeline_3d()
                await sma3d.run()

        # Optional synchronous execution for debugging: /recompute?sync=true
        sync = request.query_params.get("sync")
        if isinstance(sync, str) and sync.lower() == "true":
            await _do_recompute_3d()
            return {"status": "accepted", "message": "Recompute completed (sync)", "timeframe": "3day"}
        else:
            asyncio.create_task(_do_recompute_3d())
            return {"status": "accepted", "message": "Recompute scheduled", "timeframe": "3day"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling 3day recompute: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# In-process guard (single-worker protection). For multi-worker, rely on cooldown + ops.
_recompute_lock = asyncio.Lock()
_last_recompute_started_at: datetime | None = None


@router.post("/1day/recompute", status_code=status.HTTP_202_ACCEPTED)
async def recompute_1day(
    request: Request,
    background_tasks: BackgroundTasks,  # kept for signature stability; not used
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Secure recompute endpoint: fetch latest FMP prices and run SMA 1D pipeline.
    - Requires settings.enable_recompute_api = True
    - Requires X-Admin-Token header to match settings.admin_recompute_token (if set)
    - Enforces cooldown via DataFreshnessService and an advisory lock
    Returns 202 Accepted when background task is scheduled; client should poll GET /sectors/1day/.
    """
    try:
        if not settings.enable_recompute_api:
            raise HTTPException(status_code=403, detail="Recompute API disabled")

        # Token check
        token = request.headers.get("X-Admin-Token")
        if settings.admin_recompute_token and token != settings.admin_recompute_token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Cooldown check using freshness (deny if last batch < cooldown seconds)
        last_batch, _ = freshness_service.get_latest_complete_batch(db, timeframe="1day")
        if last_batch:
            last_ts = last_batch[0].timestamp
            age = freshness_service.get_batch_age_info(last_ts)
            # age_minutes available; compare in seconds
            if (age.get("age_minutes", 0) or 0) * 60 < settings.recompute_cooldown_seconds:
                raise HTTPException(status_code=429, detail="Recompute cooldown active")

        # In-process lock to avoid overlapping runs (single app instance)
        if _recompute_lock.locked():
            raise HTTPException(status_code=409, detail="Another recompute is in progress")

        # Background task to fetch prices then run SMA pipeline
        async def _do_recompute():
            async with _recompute_lock:
                global _last_recompute_started_at
                _last_recompute_started_at = datetime.now(timezone.utc)
                fmp = FMPBatchDataService()
                # Use existing stock_universe, not screener, to avoid drift
                symbols = [r[0] for r in db.execute(text("SELECT symbol FROM stock_universe WHERE is_active = true")).fetchall()]
                try:
                    # Fetch raw quotes in batches and store to stock_prices_1d
                    raw_quotes = await fmp.fmp_client.get_batch_quotes(symbols, 1000)
                    if raw_quotes:
                        from services.data_persistence_service import get_persistence_service
                        persistence = get_persistence_service()
                        await persistence.store_fmp_batch_price_data(raw_quotes)
                except Exception as e:
                    logger.error(f"Price fetch/store failed (continuing to analysis): {e}")
                sma = get_sma_pipeline_1d()
                await sma.run()

        # Ensure the async recompute coroutine is actually scheduled
        # Schedule async task immediately on the running event loop
        asyncio.create_task(_do_recompute())

        return {"status": "accepted", "message": "Recompute scheduled", "timeframe": "1day"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling recompute: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/1day/{sector_name}", response_model=Dict[str, Any])
async def get_sector_details_1day(
    sector_name: str,
    include_stale: bool = True,
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get detailed information for a specific sector from 1day timeframe
    """
    try:

        # Get latest complete batch for 1day timeframe
        batch_records, is_stale = freshness_service.get_latest_complete_batch(
            db, timeframe="1day"
        )

        if not batch_records:
            raise HTTPException(
                status_code=404,
                detail="No complete sector sentiment batches found for 1day timeframe",
            )

        # Find the specific sector in the batch
        sector_record = None
        for record in batch_records:
            if record.sector == sector_name:
                sector_record = record
                break

        if not sector_record:
            raise HTTPException(
                status_code=404,
                detail=f"Sector '{sector_name}' not found in latest 1day batch",
            )

        # If caller doesn't want stale data and we only have stale data
        if not include_stale and is_stale:
            raise HTTPException(
                status_code=410,
                detail="Latest 1day data is stale. Refresh analysis recommended.",
            )

        # Get batch age information
        batch_age = freshness_service.get_batch_age_info(sector_record.timestamp)

        # Build detailed response
        sector_dict = sector_record.to_dict()

        et_meta = utc_to_et_fields(sector_record.timestamp)
        response = {
            "sector": sector_dict,
            "metadata": {
                "batch_id": sector_record.batch_id,
                "timestamp": sector_record.timestamp.isoformat(),
                "timeframe": "1day",
                "is_stale": is_stale,
                "staleness_threshold_hours": 1,
                "age_minutes": batch_age["age_minutes"],
                "batch_contains_all_sectors": len(batch_records) == 11,
                **et_meta,
            },
        }

        if is_stale:
            response["warning"] = (
                "Data is stale for 1day timeframe. Consider refreshing analysis."
            )

        logger.info(
            f"Served sector {sector_name} for 1day timeframe "
            f"from batch {sector_record.batch_id} (stale: {is_stale})"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sector {sector_name} for 1day: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/1day/batch/summaries", response_model=List[Dict[str, Any]])
async def get_batch_summaries_1day(
    limit: int = 5,
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get summaries of recent 1day analysis batches for monitoring/debugging
    """
    try:
        summaries = freshness_service.get_all_batch_summaries(
            db, timeframe="1day", limit=limit
        )

        logger.info(f"Served {len(summaries)} batch summaries for 1day timeframe")
        return summaries

    except Exception as e:
        logger.error(f"Error getting batch summaries for 1day: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/1day/status/freshness", response_model=Dict[str, Any])
async def get_freshness_status_1day(
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get overall data freshness status for 1day timeframe
    """
    try:

        # Get latest batch info for 1day timeframe
        batch_records, is_stale = freshness_service.get_latest_complete_batch(
            db, timeframe="1day"
        )

        if not batch_records:
            return {
                "status": "no_data",
                "message": "No sector sentiment data available for 1day timeframe",
                "recommendation": "Run initial analysis",
                "last_analysis": None,
                "timeframe": "1day",
            }

        # Get age details
        batch_age = freshness_service.get_batch_age_info(batch_records[0].timestamp)

        # Determine status and recommendation
        if is_stale:
            if batch_age["age_minutes"] > 120:  # >2 hours
                status = "very_stale"
                recommendation = "Immediate refresh strongly recommended"
            else:
                status = "stale"
                recommendation = "Refresh recommended"
        else:
            status = "fresh"
            recommendation = "Data is current"

        et_meta = utc_to_et_fields(batch_records[0].timestamp)
        return {
            "status": status,
            "is_stale": is_stale,
            "age_minutes": batch_age["age_minutes"],
            "staleness_threshold_hours": 1,
            "last_analysis": batch_records[0].timestamp.isoformat(),
            "batch_id": batch_records[0].batch_id,
            "sector_count": len(batch_records),
            "timeframe": "1day",
            "recommendation": recommendation,
            "message": f"Data for 1day timeframe is {batch_age['age_minutes']:.1f} minutes old",
            **et_meta,
        }

    except Exception as e:
        logger.error(f"Error getting freshness status for 1day: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/comparison/{sector_name}", response_model=Dict[str, Any])
async def get_sector_timeframe_comparison(
    sector_name: str, 
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get sentiment score comparison across all timeframes for a specific sector
    Lightweight endpoint for cross-timeframe analysis
    """
    try:
        comparison = {}
        valid_timeframes = ["30min", "1day", "3day", "1week"]

        for timeframe in valid_timeframes:
            try:
                batch_records, is_stale = freshness_service.get_latest_complete_batch(
                    db, timeframe=timeframe
                )

                # Find the sector in the batch
                sector_record = None
                for record in batch_records:
                    if record.sector == sector_name:
                        sector_record = record
                        break

                if sector_record:
                    batch_age = freshness_service.get_batch_age_info(
                        sector_record.timestamp
                    )
                    comparison[timeframe] = {
                        "sentiment_score": sector_record.sentiment_score,
                        "age_minutes": batch_age["age_minutes"],
                        "is_stale": is_stale,
                        "batch_id": sector_record.batch_id,
                    }
                else:
                    comparison[timeframe] = {
                        "sentiment_score": None,
                        "error": f"Sector {sector_name} not found in {timeframe} batch",
                    }

            except Exception as e:
                comparison[timeframe] = {
                    "sentiment_score": None,
                    "error": f"Failed to get {timeframe} data: {str(e)}",
                }

        return {
            "sector": sector_name,
            "timeframe_comparison": comparison,
            "valid_timeframes": valid_timeframes,
        }

    except Exception as e:
        logger.error(f"Error getting timeframe comparison for {sector_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
