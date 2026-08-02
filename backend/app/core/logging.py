import logging

from app.core.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper(), format=_LOG_FORMAT)
