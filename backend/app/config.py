import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/trading.db"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:80", "http://localhost"]
    DEFAULT_R: float = 0.28
    DEFAULT_D: float = 0.075
    DEFAULT_MIN_N: int = 22
    MAX_STOCKS: int = 10
    MAX_POSITIONS: int = 4

    class Config:
        env_file = ".env"


settings = Settings()
