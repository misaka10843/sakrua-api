import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from rich.logging import RichHandler
from app.core.config import settings


def setup_logger():
    if not os.path.exists(settings.LOG_DIR):
        os.makedirs(settings.LOG_DIR)

    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)

    logger.handlers = []

    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_formatter = logging.Formatter("%(message)s")

    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_path=False
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(settings.LOG_LEVEL)

    log_file = os.path.join(settings.LOG_DIR, "app.log")

    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=settings.LOG_RETENTION_DAYS,
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(settings.LOG_LEVEL)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("tortoise").setLevel(logging.WARNING)

    return logger


logger = setup_logger()