"""
Analysis Scheduler - Slice 1A Implementation
Manages background analysis scheduling and on-demand analysis triggers
Hybrid system: Background (8PM/4AM/8AM) + On-demand user triggers
"""
from typing import Dict, Any, Optional, Callable
import asyncio
import logging
from datetime import datetime
from enum import Enum
import schedule
import threading
import time

from core.config import get_settings
from services.universe_builder import get_universe_builder
from services.sector_calculator import get_sector_calculator
from services.stock_ranker import get_stock_ranker

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of analysis that can be scheduled"""

    COMPREHENSIVE_DAILY = "comprehensive_daily"  # 8PM: Full universe + multi-timeframe
    OVERNIGHT_IMPACT = "overnight_impact"  # 4AM: Overnight changes
    PRE_MARKET_FINAL = "pre_market_final"  # 8AM: Economic data integration
    ON_DEMAND_FULL = "on_demand_full"  # User-triggered full refresh
    ON_DEMAND_QUICK = "on_demand_quick"  # User-triggered sector only


class AnalysisScheduler:
    """
    Manages all analysis scheduling for Slice 1A
    Implements hybrid background + on-demand system from SDD
    """

    def __init__(self):
        self.settings = get_settings()
        self.universe_builder = get_universe_builder()
        self.sector_calculator = get_sector_calculator()
        self.stock_ranker = get_stock_ranker()

        # Analysis tracking
        self.current_analysis: Optional[Dict[str, Any]] = None
        self.last_analysis: Dict[AnalysisType, Optional[datetime]] = {
            AnalysisType.COMPREHENSIVE_DAILY: None,
            AnalysisType.OVERNIGHT_IMPACT: None,
            AnalysisType.PRE_MARKET_FINAL: None,
            AnalysisType.ON_DEMAND_FULL: None,
            AnalysisType.ON_DEMAND_QUICK: None,
        }

        # Background scheduler
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_running = False

        # Progress callbacks for on-demand analysis
        self.progress_callbacks: Dict[str, Callable] = {}

    async def start_background_scheduler(self):
        """Start background analysis scheduler"""
        try:
            if self.scheduler_running:
                logger.info("Background scheduler already running")
                return

            # Schedule background analysis times
            schedule.every().day.at("20:00").do(self._run_comprehensive_daily)
            schedule.every().day.at("04:00").do(self._run_overnight_impact)
            schedule.every().day.at("08:00").do(self._run_pre_market_final)

            # Start scheduler thread
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop, daemon=True
            )
            self.scheduler_thread.start()
            self.scheduler_running = True

            logger.info("Background analysis scheduler started")

        except Exception as e:
            logger.error(f"Failed to start background scheduler: {e}")
            raise

    def _scheduler_loop(self):
        """Background scheduler loop"""
        while self.scheduler_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")

    async def _run_comprehensive_daily(self):
        """Run comprehensive daily analysis at 8PM"""
        try:
            logger.info("Starting comprehensive daily analysis")

            # Update universe
            await self.universe_builder.build_universe()

            # Calculate sector sentiment
            await self.sector_calculator.calculate_all_sectors()

            # Rank stocks
            await self.stock_ranker.rank_all_sectors()

            self.last_analysis[AnalysisType.COMPREHENSIVE_DAILY] = datetime.utcnow()
            logger.info("Comprehensive daily analysis completed")

        except Exception as e:
            logger.error(f"Comprehensive daily analysis failed: {e}")

    async def _run_overnight_impact(self):
        """Run overnight impact analysis at 4AM"""
        try:
            logger.info("Starting overnight impact analysis")

            # Quick sector sentiment update
            await self.sector_calculator.calculate_all_sectors()

            # Update stock rankings
            await self.stock_ranker.rank_all_sectors()

            self.last_analysis[AnalysisType.OVERNIGHT_IMPACT] = datetime.utcnow()
            logger.info("Overnight impact analysis completed")

        except Exception as e:
            logger.error(f"Overnight impact analysis failed: {e}")

    async def _run_pre_market_final(self):
        """Run pre-market final analysis at 8AM"""
        try:
            logger.info("Starting pre-market final analysis")

            # Final sector sentiment update
            await self.sector_calculator.calculate_all_sectors()

            # Final stock rankings
            await self.stock_ranker.rank_all_sectors()

            self.last_analysis[AnalysisType.PRE_MARKET_FINAL] = datetime.utcnow()
            logger.info("Pre-market final analysis completed")

        except Exception as e:
            logger.error(f"Pre-market final analysis failed: {e}")

    async def trigger_on_demand_analysis(
        self, analysis_type: AnalysisType, progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Trigger on-demand analysis"""
        try:
            if self.current_analysis:
                return {
                    "status": "error",
                    "message": "Analysis already in progress",
                }

            # Set up progress tracking
            analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            if progress_callback:
                self.progress_callbacks[analysis_id] = progress_callback

            self.current_analysis = {
                "id": analysis_id,
                "type": analysis_type,
                "started_at": datetime.utcnow(),
                "status": "running",
            }

            # Run analysis based on type
            if analysis_type == AnalysisType.ON_DEMAND_FULL:
                await self._run_comprehensive_daily()
            elif analysis_type == AnalysisType.ON_DEMAND_QUICK:
                await self.sector_calculator.calculate_all_sectors()

            # Update completion
            self.current_analysis["status"] = "completed"
            self.current_analysis["completed_at"] = datetime.utcnow()
            self.last_analysis[analysis_type] = datetime.utcnow()

            # Clean up
            if analysis_id in self.progress_callbacks:
                del self.progress_callbacks[analysis_id]
            self.current_analysis = None

            return {
                "status": "success",
                "analysis_id": analysis_id,
                "type": analysis_type,
                "completed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"On-demand analysis failed: {e}")
            if self.current_analysis:
                self.current_analysis["status"] = "failed"
                self.current_analysis["error"] = str(e)
            return {
                "status": "error",
                "message": str(e),
            }

    def get_analysis_status(self) -> Dict[str, Any]:
        """Get current analysis status"""
        try:
            return {
                "current_analysis": self.current_analysis,
                "last_analysis": {
                    analysis_type.value: last_time.isoformat() if last_time else None
                    for analysis_type, last_time in self.last_analysis.items()
                },
                "scheduler_running": self.scheduler_running,
            }

        except Exception as e:
            logger.error(f"Failed to get analysis status: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    def get_data_freshness(self) -> Dict[str, Any]:
        """Get data freshness information"""
        try:
            now = datetime.utcnow()
            freshness_data = {}

            for analysis_type, last_time in self.last_analysis.items():
                if last_time:
                    age_hours = (now - last_time).total_seconds() / 3600
                    freshness_data[analysis_type.value] = {
                        "last_update": last_time.isoformat(),
                        "age_hours": round(age_hours, 2),
                        "fresh": age_hours < 2,  # Less than 2 hours = fresh
                    }
                else:
                    freshness_data[analysis_type.value] = {
                        "last_update": None,
                        "age_hours": None,
                        "fresh": False,
                    }

            return {
                "freshness": freshness_data,
                "current_time": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get data freshness: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    async def stop_background_scheduler(self):
        """Stop background analysis scheduler"""
        try:
            self.scheduler_running = False
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            logger.info("Background analysis scheduler stopped")

        except Exception as e:
            logger.error(f"Failed to stop background scheduler: {e}")


# Global instance
_analysis_scheduler: Optional[AnalysisScheduler] = None


def get_analysis_scheduler() -> AnalysisScheduler:
    """Get global analysis scheduler instance"""
    global _analysis_scheduler
    if _analysis_scheduler is None:
        _analysis_scheduler = AnalysisScheduler()
    return _analysis_scheduler 