"""
Analysis Scheduler - Slice 1A Implementation
Manages background analysis scheduling and on-demand analysis triggers
Hybrid system: Background (8PM/4AM/8AM) + On-demand user triggers
"""

from typing import Dict, Any, Optional, Callable
import asyncio
import logging
from datetime import datetime, time, timezone, timedelta
from enum import Enum
import schedule
import threading
from concurrent.futures import ThreadPoolExecutor

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


class AnalysisStatus(str, Enum):
    """Status of analysis execution"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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

    def start_background_scheduler(self):
        """Start the background analysis scheduler"""
        try:
            logger.info("Starting background analysis scheduler")

            # Schedule background analysis times (Eastern Time)
            schedule.every().day.at("20:00").do(
                self._schedule_comprehensive_daily
            )  # 8 PM ET
            schedule.every().day.at("04:00").do(
                self._schedule_overnight_impact
            )  # 4 AM ET
            schedule.every().day.at("08:00").do(
                self._schedule_pre_market_final
            )  # 8 AM ET

            # Start scheduler thread
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler_loop, daemon=True
            )
            self.scheduler_thread.start()

            logger.info("Background scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start background scheduler: {e}")

    def stop_background_scheduler(self):
        """Stop the background analysis scheduler"""
        try:
            logger.info("Stopping background analysis scheduler")
            self.scheduler_running = False

            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)

            schedule.clear()
            logger.info("Background scheduler stopped")

        except Exception as e:
            logger.error(f"Error stopping background scheduler: {e}")

    def _run_scheduler_loop(self):
        """Run the background scheduler loop"""
        while self.scheduler_running:
            try:
                schedule.run_pending()
                threading.Event().wait(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

    def _schedule_comprehensive_daily(self):
        """Schedule comprehensive daily analysis (8 PM)"""
        if not self._is_analysis_running():
            asyncio.create_task(self.run_comprehensive_daily_analysis())

    def _schedule_overnight_impact(self):
        """Schedule overnight impact analysis (4 AM)"""
        if not self._is_analysis_running():
            asyncio.create_task(self.run_overnight_impact_analysis())

    def _schedule_pre_market_final(self):
        """Schedule pre-market final analysis (8 AM)"""
        if not self._is_analysis_running():
            asyncio.create_task(self.run_pre_market_final_analysis())

    async def run_comprehensive_daily_analysis(self) -> Dict[str, Any]:
        """
        8 PM Comprehensive Daily Analysis
        - Full universe rebuild and validation
        - Complete multi-timeframe sector calculation
        - Stock ranking for all sectors
        - Cache results for next day
        """
        analysis_id = f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            logger.info("Starting comprehensive daily analysis")
            self._start_analysis(AnalysisType.COMPREHENSIVE_DAILY, analysis_id)

            # Step 1: Rebuild universe (target: 1,500 stocks)
            logger.info("Step 1/4: Rebuilding stock universe")
            universe_result = await self.universe_builder.build_daily_universe()

            if universe_result["status"] != "success":
                raise Exception(
                    f"Universe build failed: {universe_result.get('message', 'Unknown error')}"
                )

            self._update_progress(25, "Universe rebuilt successfully")

            # Step 2: Calculate sector sentiment for all sectors
            logger.info("Step 2/4: Calculating sector sentiment")
            sector_result = await self.sector_calculator.calculate_all_sectors()

            if sector_result["status"] != "success":
                raise Exception(
                    f"Sector calculation failed: {sector_result.get('message', 'Unknown error')}"
                )

            self._update_progress(50, "Sector sentiment calculated")

            # Step 3: Rank stocks in all sectors
            logger.info("Step 3/4: Ranking stocks")
            ranking_result = await self.stock_ranker.rank_all_sectors()

            if ranking_result["status"] != "success":
                raise Exception(
                    f"Stock ranking failed: {ranking_result.get('message', 'Unknown error')}"
                )

            self._update_progress(75, "Stock ranking completed")

            # Step 4: Cache results for fast access
            logger.info("Step 4/4: Caching results")
            await self._cache_analysis_results(sector_result, ranking_result)

            self._update_progress(100, "Analysis completed successfully")

            result = {
                "status": "success",
                "analysis_type": AnalysisType.COMPREHENSIVE_DAILY.value,
                "analysis_id": analysis_id,
                "universe_size": universe_result.get("universe_size", 0),
                "sectors_analyzed": len(sector_result.get("sectors", {})),
                "completion_time": datetime.utcnow().isoformat(),
                "next_scheduled": "04:00 ET",
            }

            self._complete_analysis(AnalysisType.COMPREHENSIVE_DAILY, result)
            logger.info("Comprehensive daily analysis completed successfully")

            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "analysis_type": AnalysisType.COMPREHENSIVE_DAILY.value,
                "analysis_id": analysis_id,
                "error": str(e),
                "completion_time": datetime.utcnow().isoformat(),
            }

            self._fail_analysis(AnalysisType.COMPREHENSIVE_DAILY, error_result)
            logger.error(f"Comprehensive daily analysis failed: {e}")

            return error_result

    async def run_overnight_impact_analysis(self) -> Dict[str, Any]:
        """
        4 AM Overnight Impact Analysis
        - Refresh stock prices for overnight changes
        - Update sector sentiment with overnight data
        - Quick re-ranking of top performers
        """
        analysis_id = f"overnight_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            logger.info("Starting overnight impact analysis")
            self._start_analysis(AnalysisType.OVERNIGHT_IMPACT, analysis_id)

            # Step 1: Refresh universe data for overnight changes
            logger.info("Step 1/3: Refreshing universe data")
            universe_result = await self.universe_builder.refresh_universe_data()

            self._update_progress(33, "Universe data refreshed")

            # Step 2: Recalculate sector sentiment
            logger.info("Step 2/3: Recalculating sector sentiment")
            sector_result = await self.sector_calculator.calculate_all_sectors()

            self._update_progress(66, "Sector sentiment updated")

            # Step 3: Update stock rankings
            logger.info("Step 3/3: Updating stock rankings")
            ranking_result = await self.stock_ranker.rank_all_sectors()

            self._update_progress(100, "Overnight analysis completed")

            result = {
                "status": "success",
                "analysis_type": AnalysisType.OVERNIGHT_IMPACT.value,
                "analysis_id": analysis_id,
                "stocks_updated": universe_result.get("updated_count", 0),
                "sectors_analyzed": len(sector_result.get("sectors", {})),
                "completion_time": datetime.utcnow().isoformat(),
                "next_scheduled": "08:00 ET",
            }

            self._complete_analysis(AnalysisType.OVERNIGHT_IMPACT, result)
            logger.info("Overnight impact analysis completed successfully")

            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "analysis_type": AnalysisType.OVERNIGHT_IMPACT.value,
                "analysis_id": analysis_id,
                "error": str(e),
                "completion_time": datetime.utcnow().isoformat(),
            }

            self._fail_analysis(AnalysisType.OVERNIGHT_IMPACT, error_result)
            logger.error(f"Overnight impact analysis failed: {e}")

            return error_result

    async def run_pre_market_final_analysis(self) -> Dict[str, Any]:
        """
        8 AM Pre-Market Final Analysis
        - Final sector sentiment adjustments
        - Economic data integration
        - Pre-market volume analysis
        """
        analysis_id = f"premarket_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            logger.info("Starting pre-market final analysis")
            self._start_analysis(AnalysisType.PRE_MARKET_FINAL, analysis_id)

            # Step 1: Quick sector sentiment refresh
            logger.info("Step 1/2: Final sector sentiment calculation")
            sector_result = await self.sector_calculator.calculate_all_sectors()

            self._update_progress(50, "Final sector sentiment calculated")

            # Step 2: Update rankings with pre-market data
            logger.info("Step 2/2: Final stock ranking update")
            ranking_result = await self.stock_ranker.rank_all_sectors()

            self._update_progress(100, "Pre-market analysis completed")

            result = {
                "status": "success",
                "analysis_type": AnalysisType.PRE_MARKET_FINAL.value,
                "analysis_id": analysis_id,
                "sectors_analyzed": len(sector_result.get("sectors", {})),
                "completion_time": datetime.utcnow().isoformat(),
                "market_open": "09:30 ET",
                "ready_for_trading": True,
            }

            self._complete_analysis(AnalysisType.PRE_MARKET_FINAL, result)
            logger.info("Pre-market final analysis completed successfully")

            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "analysis_type": AnalysisType.PRE_MARKET_FINAL.value,
                "analysis_id": analysis_id,
                "error": str(e),
                "completion_time": datetime.utcnow().isoformat(),
            }

            self._fail_analysis(AnalysisType.PRE_MARKET_FINAL, error_result)
            logger.error(f"Pre-market final analysis failed: {e}")

            return error_result

    async def run_on_demand_analysis(
        self, analysis_type: str = "full", progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        User-triggered on-demand analysis
        - Full: Complete refresh (3-5 minutes)
        - Quick: Sector sentiment only (30 seconds)
        """
        analysis_id = f"ondemand_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Register progress callback
            if progress_callback:
                self.progress_callbacks[analysis_id] = progress_callback

            if analysis_type == "full":
                return await self._run_on_demand_full(analysis_id)
            else:
                return await self._run_on_demand_quick(analysis_id)

        except Exception as e:
            error_result = {
                "status": "error",
                "analysis_type": f"on_demand_{analysis_type}",
                "analysis_id": analysis_id,
                "error": str(e),
                "completion_time": datetime.utcnow().isoformat(),
            }

            logger.error(f"On-demand analysis failed: {e}")
            return error_result

        finally:
            # Clean up progress callback
            if analysis_id in self.progress_callbacks:
                del self.progress_callbacks[analysis_id]

    async def _run_on_demand_full(self, analysis_id: str) -> Dict[str, Any]:
        """Run full on-demand analysis (3-5 minute target)"""
        logger.info("Starting full on-demand analysis")
        self._start_analysis(AnalysisType.ON_DEMAND_FULL, analysis_id)

        # Step 1: Refresh universe
        self._update_progress(10, "Refreshing stock universe", analysis_id)
        universe_result = await self.universe_builder.refresh_universe_data()

        # Step 2: Calculate sector sentiment
        self._update_progress(40, "Calculating sector sentiment", analysis_id)
        sector_result = await self.sector_calculator.calculate_all_sectors()

        # Step 3: Update rankings
        self._update_progress(70, "Updating stock rankings", analysis_id)
        ranking_result = await self.stock_ranker.rank_all_sectors()

        # Step 4: Cache results
        self._update_progress(90, "Caching results", analysis_id)
        await self._cache_analysis_results(sector_result, ranking_result)

        self._update_progress(100, "Analysis completed", analysis_id)

        result = {
            "status": "success",
            "analysis_type": AnalysisType.ON_DEMAND_FULL.value,
            "analysis_id": analysis_id,
            "sectors_analyzed": len(sector_result.get("sectors", {})),
            "completion_time": datetime.utcnow().isoformat(),
            "duration_seconds": (
                datetime.utcnow() - self.current_analysis["start_time"]
            ).total_seconds(),
        }

        self._complete_analysis(AnalysisType.ON_DEMAND_FULL, result)
        return result

    async def _run_on_demand_quick(self, analysis_id: str) -> Dict[str, Any]:
        """Run quick on-demand analysis (30 second target)"""
        logger.info("Starting quick on-demand analysis")
        self._start_analysis(AnalysisType.ON_DEMAND_QUICK, analysis_id)

        # Quick sector sentiment calculation only
        self._update_progress(50, "Calculating sector sentiment", analysis_id)
        sector_result = await self.sector_calculator.calculate_all_sectors()

        self._update_progress(100, "Quick analysis completed", analysis_id)

        result = {
            "status": "success",
            "analysis_type": AnalysisType.ON_DEMAND_QUICK.value,
            "analysis_id": analysis_id,
            "sectors_analyzed": len(sector_result.get("sectors", {})),
            "completion_time": datetime.utcnow().isoformat(),
            "duration_seconds": (
                datetime.utcnow() - self.current_analysis["start_time"]
            ).total_seconds(),
        }

        self._complete_analysis(AnalysisType.ON_DEMAND_QUICK, result)
        return result

    def _start_analysis(self, analysis_type: AnalysisType, analysis_id: str):
        """Start tracking an analysis"""
        self.current_analysis = {
            "type": analysis_type,
            "id": analysis_id,
            "status": AnalysisStatus.RUNNING,
            "start_time": datetime.utcnow(),
            "progress": 0,
            "message": "Starting analysis...",
        }

    def _update_progress(
        self, progress: int, message: str, analysis_id: Optional[str] = None
    ):
        """Update analysis progress"""
        if self.current_analysis:
            self.current_analysis["progress"] = progress
            self.current_analysis["message"] = message

            # Call progress callback if available
            if analysis_id and analysis_id in self.progress_callbacks:
                try:
                    self.progress_callbacks[analysis_id](progress, message)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

    def _complete_analysis(self, analysis_type: AnalysisType, result: Dict[str, Any]):
        """Complete an analysis"""
        self.last_analysis[analysis_type] = datetime.utcnow()
        if self.current_analysis:
            self.current_analysis["status"] = AnalysisStatus.COMPLETED
            self.current_analysis["result"] = result
        self.current_analysis = None

    def _fail_analysis(self, analysis_type: AnalysisType, result: Dict[str, Any]):
        """Fail an analysis"""
        if self.current_analysis:
            self.current_analysis["status"] = AnalysisStatus.FAILED
            self.current_analysis["result"] = result
        self.current_analysis = None

    def _is_analysis_running(self) -> bool:
        """Check if analysis is currently running"""
        return (
            self.current_analysis is not None
            and self.current_analysis["status"] == AnalysisStatus.RUNNING
        )

    async def _cache_analysis_results(self, sector_result: Dict, ranking_result: Dict):
        """Cache analysis results for fast access"""
        # This will be implemented in the cache service
        # For now, just log that caching would happen
        logger.info("Caching analysis results for fast access")

    def get_analysis_status(self) -> Dict[str, Any]:
        """Get current analysis status"""
        return {
            "current_analysis": self.current_analysis,
            "last_analysis_times": {
                k.value: v.isoformat() if v else None
                for k, v in self.last_analysis.items()
            },
            "scheduler_running": self.scheduler_running,
        }

    def get_data_freshness(self) -> Dict[str, Any]:
        """Get data freshness information for user decisions"""
        now = datetime.utcnow()

        freshness = {}
        for analysis_type, last_time in self.last_analysis.items():
            if last_time:
                age_minutes = (now - last_time).total_seconds() / 60

                if age_minutes < 60:  # Less than 1 hour
                    freshness[analysis_type.value] = {
                        "status": "fresh",
                        "age_minutes": age_minutes,
                        "recommendation": "use_cached_data",
                    }
                elif age_minutes < 240:  # Less than 4 hours
                    freshness[analysis_type.value] = {
                        "status": "moderate",
                        "age_minutes": age_minutes,
                        "recommendation": "consider_refresh",
                    }
                else:  # More than 4 hours
                    freshness[analysis_type.value] = {
                        "status": "stale",
                        "age_minutes": age_minutes,
                        "recommendation": "refresh_recommended",
                    }
            else:
                freshness[analysis_type.value] = {
                    "status": "no_data",
                    "age_minutes": None,
                    "recommendation": "fresh_analysis_required",
                }

        return freshness

    # =====================================================
    # SLICE 1B ANALYSIS ENHANCEMENT METHODS
    # =====================================================

    async def refresh_sectors(self) -> Dict[str, Any]:
        """Refresh sector analysis (moved from sectors router)"""
        try:
            logger.info("Starting sector analysis refresh")

            # Run quick sector analysis
            result = await self.run_on_demand_analysis("quick")

            return {
                "message": "Sector analysis refresh completed",
                "status": "completed",
                "analysis_result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to refresh sectors: {e}")
            raise

    async def refresh_themes(self) -> Dict[str, Any]:
        """Refresh theme detection analysis"""
        try:
            logger.info("Starting theme detection refresh")

            # Mock theme refresh process
            await asyncio.sleep(3)  # Simulate processing time

            return {
                "message": "Theme detection refresh completed",
                "status": "completed",
                "themes_detected": 3,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to refresh themes: {e}")
            raise

    async def refresh_temperature(self) -> Dict[str, Any]:
        """Refresh temperature monitoring"""
        try:
            logger.info("Starting temperature monitoring refresh")

            # Mock temperature refresh process
            await asyncio.sleep(2)  # Simulate optimization time

            return {
                "message": "Temperature monitoring refresh completed",
                "status": "completed",
                "sectors_monitored": 8,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to refresh temperature: {e}")
            raise

    async def refresh_sympathy(self) -> Dict[str, Any]:
        """Refresh sympathy network analysis"""
        try:
            logger.info("Starting sympathy network refresh")

            # Mock sympathy refresh process
            await asyncio.sleep(2)  # Simulate processing time

            return {
                "message": "Sympathy network refresh completed",
                "status": "completed",
                "networks_updated": 3,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to refresh sympathy: {e}")
            raise


# Global instance
_analysis_scheduler: Optional[AnalysisScheduler] = None


def get_analysis_scheduler() -> AnalysisScheduler:
    """Get global analysis scheduler instance (sync, for most usage)"""
    global _analysis_scheduler
    if _analysis_scheduler is None:
        _analysis_scheduler = AnalysisScheduler()
    return _analysis_scheduler
