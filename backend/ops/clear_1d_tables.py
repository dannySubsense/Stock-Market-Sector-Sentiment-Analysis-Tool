from sqlalchemy import text
from core.database import engine


def main() -> None:
    with engine.begin() as conn:
        before_sent = conn.execute(text("SELECT COUNT(*) FROM sector_sentiment_1d")).scalar()
        before_gap = conn.execute(text("SELECT COUNT(*) FROM sector_gappers_1d")).scalar()
        print(f"Before: sector_sentiment_1d={before_sent}, sector_gappers_1d={before_gap}")

        conn.execute(text("DELETE FROM sector_gappers_1d"))
        conn.execute(text("DELETE FROM sector_sentiment_1d"))

        after_sent = conn.execute(text("SELECT COUNT(*) FROM sector_sentiment_1d")).scalar()
        after_gap = conn.execute(text("SELECT COUNT(*) FROM sector_gappers_1d")).scalar()
        print(f"After: sector_sentiment_1d={after_sent}, sector_gappers_1d={after_gap}")


if __name__ == "__main__":
    main()

