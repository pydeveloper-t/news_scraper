import logging
import os
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def get_current_env() -> str:
    try:
        return os.environ["APP_ENV"]
    except KeyError:
        return "development"


def _get_env_file() -> Path:
    env = get_current_env()
    logger.warning("Loading `%s` environment", env)
    return Path(__file__).parent / f"config/{env}.env"


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_DESTINATIONS: list = ["console"]
    
    # DATABASE_URL: str | None = None
    # ECHO_SQL: bool = False

    WORKDIR: str
    NYTIMES_EMAIL: str
    NYTIMES__PASSWORD: str


    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=_get_env_file(),
    )


settings = Settings()
