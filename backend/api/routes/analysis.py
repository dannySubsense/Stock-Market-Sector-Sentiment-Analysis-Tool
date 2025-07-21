"""
Analysis API endpoints for Slice 1B intelligence features
Handles theme detection, temperature monitoring, and sympathy networks
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.database import get_db
from services.analysis_scheduler import get_analysis_scheduler
from services.theme_detection import get_theme_detector
from services.temperature_monitor import get_temperature_monitor
from services.sympathy_network import get_sympathy_network

router = APIRouter()
logger = logging.getLogger(__name__)

# =====================================================
# SLICE 1A ANALYSIS ENDPOINTS (Moved from sectors.py)
# =====================================================


@router.post("/analysis/on-demand")
async def trigger_on_demand_analysis(
    background_tasks: BackgroundTasks,
    analysis_type: str = "full",
    db: Session = Depends(get_db),
):
    """
    Trigger on-demand analysis (moved from /sectors/analysis/on-demand)
    Enhanced for Slice 1B with theme detection integration
    """
    try:
        # Validate analysis type
        if analysis_type not in ["full", "quick"]:
            raise HTTPException(
                status_code=400, detail="analysis_type must be 'full' or 'quick'"
            )

        analysis_scheduler = get_analysis_scheduler()

        # Check if analysis is already running
        status = analysis_scheduler.get_analysis_status()
        if (
            status.get("current_analysis")
            and status["current_analysis"].get("status") == "running"
        ):
            return {
                "status": "already_running",
                "message": "Analysis is already in progress",
                "current_analysis": status["current_analysis"],
                "estimated_completion": (
                    "3-5 minutes" if analysis_type == "full" else "30 seconds"
                ),
            }

        # Start analysis in background
        if analysis_type == "full":
            background_tasks.add_task(
                analysis_scheduler.run_comprehensive_daily_analysis
            )
            estimated_time = "3-5 minutes"
        else:
            background_tasks.add_task(
                analysis_scheduler.run_on_demand_analysis, "quick"
            )
            estimated_time = "30 seconds"

        return {
            "status": "started",
            "analysis_type": analysis_type,
            "estimated_completion_time": estimated_time,
            "message": f"On-demand {analysis_type} analysis initiated",
            "includes_themes": True,  # Slice 1B feature
            "timestamp": datetime.utcnow().isoformat(),
            "check_status_url": "/api/analysis/status",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger on-demand analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start analysis: {str(e)}"
        )


@router.post("/analysis/trigger")
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    analysis_type: str = "full",
    db: Session = Depends(get_db),
):
    """
    Trigger analysis (legacy endpoint, use /analysis/on-demand instead)
    Enhanced for Slice 1B with theme detection integration
    """
    try:
        analysis_scheduler = get_analysis_scheduler()

        # Start analysis in background
        background_tasks.add_task(
            analysis_scheduler.run_analysis,
            analysis_type=analysis_type,
            include_themes=True,  # Slice 1B enhancement
        )

        return {
            "message": f"Analysis triggered successfully",
            "analysis_type": analysis_type,
            "status": "in_progress",
            "estimated_completion": "3-5 minutes",
            "includes_themes": True,  # Slice 1B feature
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to trigger analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger analysis: {str(e)}"
        )


@router.get("/analysis/status")
async def get_analysis_status():
    """
    Get analysis status (moved from /sectors/analysis/status)
    Enhanced with Slice 1B theme detection status
    """
    try:
        analysis_scheduler = get_analysis_scheduler()
        status = analysis_scheduler.get_status()

        # Add Slice 1B theme detection status
        theme_detector = get_theme_detector()
        theme_status = theme_detector.get_status()

        return {
            "analysis_status": status,
            "theme_detection_status": theme_status,  # Slice 1B
            "last_completion": status.get("last_completion"),
            "next_scheduled": status.get("next_scheduled"),
            "active_themes": theme_status.get("active_themes", []),  # Slice 1B
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get analysis status: {str(e)}"
        )


@router.post("/analysis/refresh-sectors")
async def refresh_sector_analysis(db: Session = Depends(get_db)):
    """
    Refresh sector analysis (moved from /sectors/refresh)
    Enhanced with theme contamination detection
    """
    try:
        analysis_scheduler = get_analysis_scheduler()

        # Trigger sector refresh with theme integration
        analysis_scheduler.refresh_sectors(include_themes=True)

        return {
            "message": "Sector analysis refresh completed",
            "status": "completed",
            "includes_theme_contamination": True,  # Slice 1B
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to refresh sectors: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh sectors: {str(e)}"
        )


# =====================================================
# SLICE 1B INTELLIGENCE ENDPOINTS
# =====================================================


@router.post("/analysis/theme-detection")
async def trigger_theme_detection(
    background_tasks: BackgroundTasks, scan_type: str = "comprehensive"
):
    """
    SLICE 1B: Trigger theme detection scan
    Identifies cross-sector narratives and contamination
    """
    try:
        theme_detector = get_theme_detector()

        # Start theme detection in background
        background_tasks.add_task(theme_detector.scan_for_themes, scan_type=scan_type)

        return {
            "message": "Theme detection scan initiated",
            "scan_type": scan_type,
            "status": "in_progress",
            "estimated_completion": "10-15 minutes",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to trigger theme detection: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger theme detection: {str(e)}"
        )


@router.get("/analysis/themes/active")
async def get_active_themes():
    """
    SLICE 1B: Get currently active themes
    Returns themes affecting sector sentiment
    """
    try:
        theme_detector = get_theme_detector()
        active_themes = theme_detector.get_active_themes()

        return {
            "active_themes": active_themes,
            "theme_count": len(active_themes),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get active themes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get active themes: {str(e)}"
        )


@router.get("/analysis/themes/{theme_id}")
async def get_theme_details(theme_id: str):
    """
    SLICE 1B: Get specific theme details
    Returns detailed information about a theme
    """
    try:
        theme_detector = get_theme_detector()
        theme_details = theme_detector.get_theme_details(theme_id)

        if not theme_details:
            raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")

        return {"theme": theme_details, "timestamp": datetime.utcnow().isoformat()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get theme details: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get theme details: {str(e)}"
        )


@router.get("/analysis/themes/{theme_id}/stocks")
async def get_theme_affected_stocks(theme_id: str):
    """
    SLICE 1B: Get stocks affected by a specific theme
    Returns stocks with theme contamination risk
    """
    try:
        theme_detector = get_theme_detector()
        affected_stocks = theme_detector.get_theme_affected_stocks(theme_id)

        return {
            "theme_id": theme_id,
            "affected_stocks": affected_stocks,
            "stock_count": len(affected_stocks),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get theme affected stocks: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get theme affected stocks: {str(e)}"
        )


@router.get("/analysis/temperature")
async def get_all_sector_temperatures():
    """
    SLICE 1B: Get all sector temperatures
    Returns momentum temperature for all sectors
    """
    try:
        temp_monitor = get_temperature_monitor()
        temperatures = temp_monitor.get_all_sector_temperatures()

        return {
            "sector_temperatures": temperatures,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get sector temperatures: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sector temperatures: {str(e)}"
        )


@router.get("/analysis/temperature/{sector}")
async def get_sector_temperature(sector: str):
    """
    SLICE 1B: Get specific sector temperature
    Returns momentum temperature for a sector
    """
    try:
        temp_monitor = get_temperature_monitor()
        temperature = temp_monitor.get_sector_temperature(sector)

        if not temperature:
            raise HTTPException(
                status_code=404,
                detail=f"Temperature data for sector '{sector}' not found",
            )

        return {
            "sector": sector,
            "temperature": temperature,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sector temperature: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sector temperature: {str(e)}"
        )


@router.post("/analysis/temperature/monitor")
async def start_temperature_monitoring():
    """
    SLICE 1B: Start temperature monitoring
    Initiates real-time momentum tracking
    """
    try:
        temp_monitor = get_temperature_monitor()
        temp_monitor.start_monitoring()

        return {
            "message": "Temperature monitoring started",
            "status": "active",
            "frequency": "hourly",
            "sessions": "4 AM - 8 PM ET",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to start temperature monitoring: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start temperature monitoring: {str(e)}"
        )


@router.get("/analysis/temperature/alerts")
async def get_temperature_alerts():
    """
    SLICE 1B: Get temperature alerts
    Returns alerts for extreme temperature conditions
    """
    try:
        temp_monitor = get_temperature_monitor()
        alerts = temp_monitor.get_alerts()

        return {
            "temperature_alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get temperature alerts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get temperature alerts: {str(e)}"
        )


@router.get("/analysis/sympathy/{symbol}")
async def get_sympathy_network(symbol: str):
    """
    SLICE 1B: Get sympathy network for a symbol
    Returns correlated stocks and prediction confidence
    """
    try:
        sympathy_network = get_sympathy_network()
        network = sympathy_network.get_network_for_symbol(symbol)

        return {
            "symbol": symbol,
            "sympathy_network": network,
            "network_size": len(network.get("correlated_stocks", [])),
            "prediction_confidence": network.get("confidence", 0.0),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get sympathy network: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sympathy network: {str(e)}"
        )


@router.post("/analysis/sympathy/update")
async def update_sympathy_networks():
    """
    SLICE 1B: Update sympathy networks
    Recalculates correlation matrices
    """
    try:
        sympathy_network = get_sympathy_network()
        sympathy_network.update_networks()

        return {
            "message": "Sympathy networks updated",
            "status": "completed",
            "universe_size": 1500,  # Small-cap universe
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to update sympathy networks: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update sympathy networks: {str(e)}"
        )


@router.get("/analysis/sympathy/alerts")
async def get_sympathy_alerts():
    """
    SLICE 1B: Get sympathy alerts
    Returns alerts for sympathy network movements
    """
    try:
        sympathy_network = get_sympathy_network()
        alerts = sympathy_network.get_alerts()

        return {
            "sympathy_alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get sympathy alerts: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sympathy alerts: {str(e)}"
        )
