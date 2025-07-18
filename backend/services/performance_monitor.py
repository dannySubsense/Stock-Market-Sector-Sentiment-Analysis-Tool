"""
Performance Monitor Service for Slice 1B
Handles cache performance monitoring and optimization recommendations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring engine for Slice 1B intelligence"""

    def __init__(self):
        self.cache_metrics = {
            "hit_rate": 0.92,
            "miss_rate": 0.08,
            "total_requests": 15420,
            "cache_size": 256,
            "response_time_avg": 45,  # milliseconds
            "memory_usage": 0.75,  # percentage
        }
        self.access_patterns = {}

    async def get_cache_performance(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        try:
            return {
                "cache_metrics": self.cache_metrics,
                "performance_score": self._calculate_performance_score(),
                "status": (
                    "healthy" if self.cache_metrics["hit_rate"] > 0.9 else "degraded"
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get cache performance: {e}")
            raise

    async def get_detailed_cache_performance(self) -> Dict[str, Any]:
        """Get detailed cache performance analysis"""
        try:
            performance_score = self._calculate_performance_score()

            recommendations = []
            if self.cache_metrics["hit_rate"] < 0.9:
                recommendations.append("Consider increasing cache size or TTL")
            if self.cache_metrics["response_time_avg"] > 100:
                recommendations.append(
                    "Cache response time is high, investigate bottlenecks"
                )
            if self.cache_metrics["memory_usage"] > 0.8:
                recommendations.append(
                    "Cache memory usage is high, consider optimization"
                )

            optimization_opportunities = []
            if self.cache_metrics["miss_rate"] > 0.1:
                optimization_opportunities.append(
                    "High miss rate indicates cache warming opportunities"
                )
            if self.cache_metrics["hit_rate"] < 0.85:
                optimization_opportunities.append(
                    "Low hit rate suggests cache strategy needs review"
                )

            return {
                "performance_score": performance_score,
                "recommendations": recommendations,
                "optimization_opportunities": optimization_opportunities,
                "detailed_metrics": self.cache_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get detailed cache performance: {e}")
            raise

    async def get_cache_access_patterns(self) -> Dict[str, Any]:
        """Get cache access pattern analysis"""
        try:
            # Mock access patterns
            hot_keys = [
                {
                    "key": "sectors_all",
                    "access_count": 1250,
                    "last_access": datetime.utcnow().isoformat(),
                },
                {
                    "key": "technology_sector",
                    "access_count": 890,
                    "last_access": datetime.utcnow().isoformat(),
                },
                {
                    "key": "healthcare_sector",
                    "access_count": 756,
                    "last_access": datetime.utcnow().isoformat(),
                },
            ]

            cold_keys = [
                {
                    "key": "utilities_sector",
                    "access_count": 45,
                    "last_access": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                },
                {
                    "key": "materials_sector",
                    "access_count": 32,
                    "last_access": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                },
            ]

            access_frequency = {
                "sectors_all": 1250,
                "technology_sector": 890,
                "healthcare_sector": 756,
                "energy_sector": 543,
                "financial_sector": 432,
                "utilities_sector": 45,
                "materials_sector": 32,
            }

            return {
                "hot_keys": hot_keys,
                "cold_keys": cold_keys,
                "access_frequency": access_frequency,
                "pattern_analysis": {
                    "most_accessed": "sectors_all",
                    "least_accessed": "materials_sector",
                    "access_distribution": "skewed_towards_sectors",
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get cache access patterns: {e}")
            raise

    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        try:
            # Weighted scoring based on key metrics
            hit_rate_score = self.cache_metrics["hit_rate"] * 40  # 40% weight
            response_time_score = (
                max(0, (100 - self.cache_metrics["response_time_avg"]) / 100) * 30
            )  # 30% weight
            memory_score = (1 - self.cache_metrics["memory_usage"]) * 20  # 20% weight
            request_volume_score = (
                min(1, self.cache_metrics["total_requests"] / 10000) * 10
            )  # 10% weight

            total_score = (
                hit_rate_score
                + response_time_score
                + memory_score
                + request_volume_score
            )
            return round(total_score, 2)

        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 0.0


# Singleton instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get performance monitor singleton instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
