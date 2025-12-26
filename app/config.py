from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Expense Tracker"
    DATABASE_URL: str = "sqlite:///C:/Users/100ca/finance_local.db"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()
