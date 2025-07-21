import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.stock_data import Base, StockPrice1D


@pytest.fixture
def db_session():
    """Create in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_stock_price_data():
    """Sample stock price data for testing."""
    return {
        "symbol": "SOUN",
        "timestamp": datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
        "open_price": 10.50,
        "high_price": 11.25,
        "low_price": 10.25,
        "close_price": 11.00,
        "volume": 1500000,
    }


class TestStockPrice1D:
    """Test suite for StockPrice1D model."""

    def test_stock_price_1d_creation_with_valid_data(
        self, db_session, sample_stock_price_data
    ):
        """Test StockPrice1D model creates with valid data."""
        stock_price = StockPrice1D(**sample_stock_price_data)
        db_session.add(stock_price)
        db_session.commit()

        retrieved = (
            db_session.query(StockPrice1D).filter(StockPrice1D.symbol == "SOUN").first()
        )

        assert retrieved is not None
        assert retrieved.symbol == "SOUN"
        assert retrieved.close_price == 11.00
        assert retrieved.volume == 1500000

    def test_stock_price_1d_requires_symbol_and_timestamp(self, db_session):
        """Test that symbol and timestamp are required primary keys."""
        with pytest.raises(Exception):
            stock_price = StockPrice1D(
                open_price=10.50, close_price=11.00, volume=1000000
            )
            db_session.add(stock_price)
            db_session.commit()

    def test_stock_price_1d_handles_null_prices(self, db_session):
        """Test model handles null price values gracefully."""
        stock_price = StockPrice1D(
            symbol="TEST",
            timestamp=datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            open_price=None,
            high_price=None,
            low_price=None,
            close_price=None,
            volume=1000000,
        )
        db_session.add(stock_price)
        db_session.commit()

        retrieved = (
            db_session.query(StockPrice1D).filter(StockPrice1D.symbol == "TEST").first()
        )

        assert retrieved is not None
        assert retrieved.open_price is None
        assert retrieved.volume == 1000000

    def test_stock_price_1d_multiple_timestamps_same_symbol(self, db_session):
        """Test storing multiple timestamps for same symbol."""
        # Use timezone-naive timestamps for SQLite compatibility
        timestamp1 = datetime(2025, 1, 21, 9, 30, 0)
        timestamp2 = datetime(2025, 1, 21, 10, 30, 0)

        price1 = StockPrice1D(
            symbol="MULTI", timestamp=timestamp1, close_price=10.00, volume=1000000
        )
        price2 = StockPrice1D(
            symbol="MULTI", timestamp=timestamp2, close_price=10.50, volume=1100000
        )

        db_session.add(price1)
        db_session.commit()

        db_session.add(price2)
        db_session.commit()

        results = (
            db_session.query(StockPrice1D).filter(StockPrice1D.symbol == "MULTI").all()
        )

        assert len(results) == 2
        assert {r.close_price for r in results} == {10.00, 10.50}

    def test_stock_price_1d_created_at_auto_timestamp(
        self, db_session, sample_stock_price_data
    ):
        """Test that created_at timestamp is automatically set."""
        stock_price = StockPrice1D(**sample_stock_price_data)
        db_session.add(stock_price)
        db_session.commit()

        retrieved = (
            db_session.query(StockPrice1D).filter(StockPrice1D.symbol == "SOUN").first()
        )

        assert retrieved.created_at is not None
        assert isinstance(retrieved.created_at, datetime)

    def test_stock_price_1d_volume_handles_large_numbers(self, db_session):
        """Test model handles large volume numbers correctly."""
        large_volume = 50000000  # 50M shares
        stock_price = StockPrice1D(
            symbol="LARGE",
            timestamp=datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            close_price=5.00,
            volume=large_volume,
        )
        db_session.add(stock_price)
        db_session.commit()

        retrieved = (
            db_session.query(StockPrice1D)
            .filter(StockPrice1D.symbol == "LARGE")
            .first()
        )

        assert retrieved.volume == large_volume

    def test_stock_price_1d_price_precision_handling(self, db_session):
        """Test that price fields handle decimal precision correctly."""
        precise_price = 123.4567
        stock_price = StockPrice1D(
            symbol="PRECISE",
            timestamp=datetime(2025, 1, 21, 9, 30, 0, tzinfo=timezone.utc),
            open_price=precise_price,
            high_price=precise_price + 1,
            low_price=precise_price - 1,
            close_price=precise_price + 0.5,
            volume=1000000,
        )
        db_session.add(stock_price)
        db_session.commit()

        retrieved = (
            db_session.query(StockPrice1D)
            .filter(StockPrice1D.symbol == "PRECISE")
            .first()
        )

        assert abs(retrieved.open_price - precise_price) < 0.001
        assert abs(retrieved.close_price - (precise_price + 0.5)) < 0.001
