"""
Logging system for resume PDF builder.
Provides structured logging with file and console handlers.
"""

import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from .config import Config


def get_logger(name: str = None) -> logging.Logger:
    """
    Get or create a logger with the specified name.

    Args:
        name: Logger name. If None, uses the caller's module name.

    Returns:
        Configured logger instance.
    """
    config = Config()
    log_dir = Path(config.output_dir) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / 'app.log'

    # Create logger
    logger = logging.getLogger(name or 'resume_pdf_builder')
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)

    # File handler (DEBUG level, rotation)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return get_logger(name)
