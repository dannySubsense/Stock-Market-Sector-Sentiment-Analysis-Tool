"""
Sector Calculator

Simplified sector performance calculator using simple average approach.
Replaces complex weighted calculations with simple average of changes_percentage.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SectorCalculator:
    """Simplified sector performance calculator supporting A/B calc modes"""

    def __init__(self, mode: str = "simple"):
        # mode: 'simple' | 'weighted'
        self.mode = mode

    def calculate_sector_performance(self, stocks: List[Dict]) -> float:
        """Calculate sector performance (percent units).

        - simple: unweighted mean of changes_percentage
        - weighted: trimmed dollar-volume weighted mean
        """
        if not stocks:
            return 0.0

        try:
            # Extract changes_percentage values
            changes = [
                stock.get("changes_percentage", 0.0)
                for stock in stocks
                if stock.get("changes_percentage") is not None
            ]

            if not changes:
                return 0.0

            if self.mode == "weighted":
                # Build dollar volume weights and clamp outliers
                values: List[float] = []
                weights: List[float] = []
                for st in stocks:
                    cp = st.get("changes_percentage")
                    if cp is None:
                        continue
                    # Trim change% to [-30, 30] to reduce tail influence
                    cp_trim = max(min(float(cp), 30.0), -30.0)
                    price = float(st.get("current_price", 0.0) or 0.0)
                    vol = float(st.get("volume", 0.0) or 0.0)
                    w = max(price * vol, 0.0)
                    values.append(cp_trim)
                    weights.append(w)

                if not values or not any(weights):
                    return round(sum(changes) / len(changes), 4)

                # Cap weights at 95th percentile
                try:
                    import numpy as np  # type: ignore

                    w_arr = np.array(weights, dtype=float)
                    cap = float(np.percentile(w_arr, 95))
                    w_arr = np.minimum(w_arr, cap)
                    v_arr = np.array(values, dtype=float)
                    perf = float((v_arr * w_arr).sum() / (w_arr.sum() or 1.0))
                    return round(perf, 4)
                except Exception:
                    # Fallback to simple mean if numpy unavailable
                    total_w = 0.0
                    total_vw = 0.0
                    # Compute capped weights without numpy
                    sorted_w = sorted(weights)
                    idx = int(0.95 * (len(sorted_w) - 1))
                    cap = sorted_w[idx] if sorted_w else 0.0
                    for v, w in zip(values, weights):
                        ww = min(w, cap)
                        total_w += ww
                        total_vw += v * ww
                    if total_w == 0:
                        return round(sum(changes) / len(changes), 4)
                    return round(total_vw / total_w, 4)

            # Default simple average in percent units (validated semantics)
            performance = sum(changes) / len(changes)
            return round(performance, 4)

        except Exception as e:
            logger.error(f"Error calculating sector performance: {e}")
            return 0.0

    def get_top_gainers_losers(self, stocks: List[Dict]) -> Dict[str, Any]:
        """Get top gainers and losers by percentage change"""
        if not stocks:
            return {"top_gainers": [], "top_losers": []}

        try:
            # Filter stocks with valid changes_percentage
            valid_stocks = [
                stock for stock in stocks if stock.get("changes_percentage") is not None
            ]

            if not valid_stocks:
                return {"top_gainers": [], "top_losers": []}

            # Sort by changes_percentage (descending for gainers, ascending for losers)
            sorted_by_gain = sorted(
                valid_stocks,
                key=lambda x: x.get("changes_percentage", 0.0),
                reverse=True,
            )

            sorted_by_loss = sorted(
                valid_stocks, key=lambda x: x.get("changes_percentage", 0.0)
            )

            # Get top 3 gainers (highest positive changes)
            top_gainers = [
                {
                    "symbol": stock.get("symbol", ""),
                    "changes_percentage": stock.get("changes_percentage", 0.0),
                    "volume": stock.get("volume", 0),
                    "current_price": stock.get("current_price", 0.0),
                }
                for stock in sorted_by_gain[:3]
                if stock.get("changes_percentage", 0.0) > 0  # Only positive changes
            ]

            # Get top 3 losers (lowest negative changes)
            top_losers = [
                {
                    "symbol": stock.get("symbol", ""),
                    "changes_percentage": stock.get("changes_percentage", 0.0),
                    "volume": stock.get("volume", 0),
                    "current_price": stock.get("current_price", 0.0),
                }
                for stock in sorted_by_loss[:3]
                if stock.get("changes_percentage", 0.0) < 0  # Only negative changes
            ]

            return {"top_gainers": top_gainers, "top_losers": top_losers}

        except Exception as e:
            logger.error(f"Error getting top gainers/losers: {e}")
            return {"top_gainers": [], "top_losers": []}
