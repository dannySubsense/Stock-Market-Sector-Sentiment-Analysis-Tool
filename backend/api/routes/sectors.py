"""
Sectors API Routes
Separate endpoints per timeframe for optimal performance and caching
Updated to use atomic batch operations with staleness detection
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from core.database import get_db
from services.data_freshness_service import get_freshness_service, DataFreshnessService

router = APIRouter(prefix="/sectors", tags=["sectors"])
logger = logging.getLogger(__name__)


@router.get("/1day/", response_model=Dict[str, Any])
async def get_all_sectors_1day(
    include_stale: bool = True,
    db: Session = Depends(get_db),
    freshness_service: DataFreshnessService = Depends(get_freshness_service),
):
    """
    Get all sector sentiment data for 1day timeframe
    Returns all 11 sectors with unified staleness flag for UI gray card display
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
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all sectors for 1day: {e}")
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
