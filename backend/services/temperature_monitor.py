"""
Temperature Monitoring Service for Slice 1B
Handles real-time momentum tracking and temperature classification
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)


class TemperatureMonitor:
    """Temperature monitoring engine for Slice 1B intelligence"""

    def __init__(self):
        self.sector_temperatures = {}
        self.monitoring_active = False
        self.temperature_thresholds = {
            "COLD": {"min": 0, "max": 5},
            "WARM": {"min": 5, "max": 15},
            "HOT": {"min": 15, "max": 25},
            "EXTREME": {"min": 25, "max": 100},
        }

    async def start_monitoring(self) -> Dict[str, Any]:
        """Start temperature monitoring for all sectors"""
        try:
            logger.info("Starting temperature monitoring")
            self.monitoring_active = True

            # Initialize sector temperatures
            sectors = [
                "technology",
                "healthcare",
                "energy",
                "financial",
                "consumer_discretionary",
                "industrials",
                "materials",
                "utilities",
            ]

            for sector in sectors:
                self.sector_temperatures[sector] = {
                    "temperature": "COLD",
                    "momentum_score": 0.0,
                    "volume_multiple": 1.0,
                    "last_update": datetime.utcnow().isoformat(),
                }

            return {
                "status": "active",
                "sectors_monitored": len(sectors),
                "frequency": "hourly",
                "started_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to start temperature monitoring: {e}")
            raise

    async def get_all_sector_temperatures(self) -> Dict[str, Any]:
        """Get temperature data for all sectors"""
        try:
            return {
                "sector_temperatures": self.sector_temperatures,
                "monitoring_active": self.monitoring_active,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get sector temperatures: {e}")
            raise

    async def get_sector_temperature(self, sector: str) -> Optional[Dict[str, Any]]:
        """Get temperature data for a specific sector"""
        try:
            if sector not in self.sector_temperatures:
                return None

            temp_data = self.sector_temperatures[sector]

            return {
                "sector": sector,
                "temperature": temp_data["temperature"],
                "momentum_score": temp_data["momentum_score"],
                "volume_multiple": temp_data["volume_multiple"],
                "last_update": temp_data["last_update"],
                "trading_recommendation": self._get_trading_recommendation(
                    temp_data["temperature"]
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get sector temperature: {e}")
            raise

    async def calculate_temperature(self, symbol: str) -> Dict[str, Any]:
        """Calculate temperature for a specific stock"""
        try:
            # Mock temperature calculation
            import random

            momentum_score = random.uniform(0, 50)  # 0-50% move
            volume_multiple = random.uniform(1, 10)  # 1-10x volume
            news_catalyst = random.choice([True, False])
            social_mentions = random.randint(0, 1000)
            short_interest = random.uniform(0.1, 0.5)

            # Determine temperature classification
            if momentum_score >= 25 and volume_multiple >= 4:
                temperature = "EXTREME"
                squeeze_risk = 0.9
                trading_recommendation = "AVOID ALL SHORTS"
            elif momentum_score >= 15 and volume_multiple >= 2.5:
                temperature = "HOT"
                squeeze_risk = 0.7
                trading_recommendation = "HIGH RISK - AVOID SHORTS"
            elif momentum_score >= 5 and volume_multiple >= 1.5:
                temperature = "WARM"
                squeeze_risk = 0.3
                trading_recommendation = "INCREASED CAUTION"
            else:
                temperature = "COLD"
                squeeze_risk = 0.1
                trading_recommendation = "NORMAL ANALYSIS APPLIES"

            return {
                "symbol": symbol,
                "classification": temperature,
                "momentum_score": momentum_score,
                "volume_multiple": volume_multiple,
                "squeeze_risk": squeeze_risk,
                "trading_recommendation": trading_recommendation,
                "momentum_velocity": momentum_score / 100,  # Normalized velocity
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to calculate temperature: {e}")
            raise

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get temperature alerts for extreme conditions"""
        try:
            alerts = []

            # Check for extreme temperatures
            for sector, temp_data in self.sector_temperatures.items():
                if temp_data["temperature"] in ["HOT", "EXTREME"]:
                    alerts.append(
                        {
                            "sector": sector,
                            "temperature": temp_data["temperature"],
                            "alert_type": "HIGH_TEMPERATURE",
                            "message": f"{sector} sector showing {temp_data['temperature']} temperature",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            # Mock some alerts
            if not alerts:
                alerts.append(
                    {
                        "sector": "technology",
                        "temperature": "HOT",
                        "alert_type": "MOCK_ALERT",
                        "message": "Technology sector showing HOT temperature due to AI theme",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            return alerts

        except Exception as e:
            logger.error(f"Failed to get temperature alerts: {e}")
            raise

    def _get_trading_recommendation(self, temperature: str) -> str:
        """Get trading recommendation based on temperature"""
        recommendations = {
            "COLD": "NORMAL ANALYSIS APPLIES",
            "WARM": "INCREASED CAUTION",
            "HOT": "HIGH RISK - AVOID SHORTS",
            "EXTREME": "AVOID ALL SHORTS",
        }
        return recommendations.get(temperature, "UNKNOWN")


# Singleton instance
_temperature_monitor = None


def get_temperature_monitor() -> TemperatureMonitor:
    """Get temperature monitor singleton instance"""
    global _temperature_monitor
    if _temperature_monitor is None:
        _temperature_monitor = TemperatureMonitor()
    return _temperature_monitor
