from datetime import datetime, timedelta, timezone

from core.database import SessionLocal, engine
from models.sector_sentiment_3d import SectorSentiment3D
from services.data_freshness_service import DataFreshnessService


def _insert_complete_3d_batch(delta_hours: int = 0) -> str:
    """Insert 11-sector 3D batch with timestamp now - delta_hours."""
    # Ensure table exists for test environment
    SectorSentiment3D.__table__.create(bind=engine, checkfirst=True)
    batch_id = f"test3d_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    # Use naive UTC to match table's TIMESTAMP column
    ts = (datetime.utcnow() - timedelta(hours=delta_hours)).replace(tzinfo=None)
    sectors = [
        "basic_materials",
        "communication_services",
        "consumer_cyclical",
        "consumer_defensive",
        "energy",
        "financial_services",
        "healthcare",
        "industrials",
        "real_estate",
        "technology",
        "utilities",
    ]
    with SessionLocal() as db:
        # Cleanup any prior 3D data to isolate test behavior
        db.query(SectorSentiment3D).delete(synchronize_session=False)
        for s in sectors:
            db.add(
                SectorSentiment3D(
                    sector=s,
                    timestamp=ts,
                    batch_id=batch_id,
                    sentiment_score=0.0,
                )
            )
        db.commit()
    return batch_id


def test_freshness_service_3d_staleness_threshold():
    svc = DataFreshnessService()

    # fresh batch (< 24h)
    _insert_complete_3d_batch(delta_hours=1)
    with SessionLocal() as db:
        recs, is_stale = svc.get_latest_complete_batch(db, timeframe="3day")
        assert len(recs) == 11
        assert is_stale is False

    # stale batch (>= 24h)
    _insert_complete_3d_batch(delta_hours=25)
    with SessionLocal() as db:
        recs, is_stale = svc.get_latest_complete_batch(db, timeframe="3day")
        assert len(recs) == 11
        assert is_stale is True


