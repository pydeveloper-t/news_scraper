import logging
import os
import sys
from enum import StrEnum
from logging.handlers import TimedRotatingFileHandler

from settings import settings

log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class LogDestinations(StrEnum):
    FILE = "file"
    CONSOLE = "console"


log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def init_logger(app_name: str | None = None, log_level: str | None = None) -> logging.Logger:
    log_destinations = [destination.lower() for destination in settings.LOG_DESTINATIONS]

    if log_level is None:
        log_level = settings.LOG_LEVEL.upper()

    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)

    # Clear any previously attached handlers
    logger.handlers.clear()

    # Set the logging destination
    if LogDestinations.FILE in log_destinations:
        logger.addHandler(_get_file_rotating_handler())
    if LogDestinations.CONSOLE in log_destinations:
        logger.addHandler(_get_stream_handler())

    return logger




def _get_file_rotating_handler():
    logdir = _create_logs_dir_if_not_exists()

    handler = TimedRotatingFileHandler(f"{logdir}/crawlers.log", when="midnight", backupCount=3)

    handler.setFormatter(log_format)
    return handler


def _get_stream_handler():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)
    return handler


def _create_logs_dir_if_not_exists() -> str:
    logdir = os.path.join(settings.WORKDIR, 'log')
    os.makedirs(logdir, exist_ok=True)
    return logdir


logger = init_logger()