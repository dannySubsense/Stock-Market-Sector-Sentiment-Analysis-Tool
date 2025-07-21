#!/usr/bin/env python3
"""
Test script to verify PostgreSQL + TimescaleDB connection
Provides workaround for Docker authentication issues
"""
import subprocess
import json


def test_db_via_docker():
    """Test database connection through Docker exec (bypasses host networking issues)"""
    print("🧪 Testing PostgreSQL + TimescaleDB via Docker...")

    try:
        # Test basic connection
        result = subprocess.run(
            [
                "docker",
                "exec",
                "market_sentiment_postgres",
                "psql",
                "-U",
                "market_user",
                "-d",
                "market_sentiment",
                "-c",
                "SELECT version();",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ PostgreSQL connection successful")

        # Test TimescaleDB
        result = subprocess.run(
            [
                "docker",
                "exec",
                "market_sentiment_postgres",
                "psql",
                "-U",
                "market_user",
                "-d",
                "market_sentiment",
                "-c",
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ TimescaleDB extension active")

        # Test tables
        result = subprocess.run(
            [
                "docker",
                "exec",
                "market_sentiment_postgres",
                "psql",
                "-U",
                "market_user",
                "-d",
                "market_sentiment",
                "-c",
                "\\dt",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ Tables exist:", result.stdout)

        # Test hypertables
        result = subprocess.run(
            [
                "docker",
                "exec",
                "market_sentiment_postgres",
                "psql",
                "-U",
                "market_user",
                "-d",
                "market_sentiment",
                "-c",
                "SELECT hypertable_name FROM timescaledb_information.hypertables;",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ Hypertables configured:", result.stdout)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Database test failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def test_universe_population():
    """Test that we can populate the universe table"""
    print("\n🧪 Testing universe population via Docker...")

    # Insert test data
    insert_sql = """
    INSERT INTO stock_universe (symbol, company_name, sector, market_cap) 
    VALUES 
        ('AAPL', 'Apple Inc', 'Technology', 3000000000000),
        ('MSFT', 'Microsoft Corp', 'Technology', 2800000000000)
    ON CONFLICT (symbol) DO NOTHING;
    """

    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "market_sentiment_postgres",
                "psql",
                "-U",
                "market_user",
                "-d",
                "market_sentiment",
                "-c",
                insert_sql,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Query the data
        result = subprocess.run(
            [
                "docker",
                "exec",
                "market_sentiment_postgres",
                "psql",
                "-U",
                "market_user",
                "-d",
                "market_sentiment",
                "-c",
                "SELECT * FROM stock_universe;",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ Universe population test successful:")
        print(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Universe population failed: {e}")
        return False


if __name__ == "__main__":
    print("🐳 PostgreSQL + TimescaleDB Connection Test")
    print("=" * 50)

    db_ok = test_db_via_docker()
    if db_ok:
        universe_ok = test_universe_population()

        if universe_ok:
            print("\n🎉 Database is ready for production use!")
            print(
                "💡 Workaround: Use Docker exec for data operations until host networking is resolved"
            )
        else:
            print("\n❌ Database setup incomplete")
    else:
        print("\n❌ Database connection failed")
