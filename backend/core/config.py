"""
Configuration management for Market Sector Sentiment Analysis Tool
Handles credentials, database settings, and environment variables
"""

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import yaml
from pathlib import Path
import os


class APIKeyConfig(BaseModel):
    """API key configuration"""

    key: str
    tier: str = "basic"


class DatabaseConfig(BaseModel):
    """Database configuration"""

    sqlite_path: str = "./data/sentiment.db"


class RedisConfig(BaseModel):
    """Redis configuration"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0


class DevelopmentConfig(BaseModel):
    """Development configuration"""

    debug: bool = True
    log_level: str = "INFO"


class CredentialsConfig(BaseModel):
    """Credentials configuration loaded from YAML"""

    api_keys: dict[str, APIKeyConfig]
    database: DatabaseConfig
    redis: RedisConfig
    development: DevelopmentConfig


class Settings(BaseSettings):
    """Main application settings"""

    # Environment variables
    environment: str = "development"
    debug: bool = True

    # API Settings
    api_v1_prefix: str = "/api"
    cors_origins: List[str] = ["http://localhost:3000"]

    # Trading Hours (Eastern Time)
    market_open_hour: int = 9
    market_open_minute: int = 30
    market_close_hour: int = 16
    market_close_minute: int = 0

    # Data Refresh Intervals (in seconds)
    sector_refresh_interval: int = 900  # 15 minutes
    stock_refresh_interval: int = 300  # 5 minutes
    news_refresh_interval: int = 600  # 10 minutes

    # Analysis Thresholds
    extreme_gap_threshold: float = 0.30  # 30%
    large_gap_threshold: float = 0.15  # 15%
    shortability_high_risk: int = 7  # 7+ points
    shortability_medium_risk: int = 4  # 4-6 points

    # Loaded credentials
    credentials: Optional[CredentialsConfig] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def load_credentials() -> CredentialsConfig:
    """Load credentials from YAML file"""
    # Look for credentials.yml in the parent directory (project root)
    credentials_path = Path(__file__).parent.parent.parent / "credentials.yml"

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found at {credentials_path}. "
            "Please create it from credentials.template.yml"
        )

    with open(credentials_path, "r") as f:
        data = yaml.safe_load(f)

    # Convert nested dictionaries to APIKeyConfig objects
    api_keys = {}
    for key, config in data.get("api_keys", {}).items():
        if isinstance(config, dict):
            api_keys[key] = APIKeyConfig(**config)
        else:
            # Handle simple string format
            api_keys[key] = APIKeyConfig(key=config)

    data["api_keys"] = api_keys

    return CredentialsConfig(**data)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
        try:
            _settings.credentials = load_credentials()
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            print("Running without credentials - some features may not work")
    return _settings
