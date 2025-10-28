"""
Sistema de logging centralizado.
Implementa ILogger interface con diferentes niveles de log.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from ..interfaces import ILogger
from ..config.app_config import config


class Logger(ILogger):
    """Logger centralizado con configuración flexible."""

    def __init__(self, name: str = "marketing_script", level: int = logging.INFO):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        self._logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # File handler (optional)
        log_file = config.get_database_path().parent / f"{name}.log"
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.WARNING)  # Only warnings and errors to file
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
        except Exception:
            # If file logging fails, continue without it
            pass

    def info(self, message: str) -> None:
        self._logger.info(message)

    def error(self, message: str, exc: Optional[Exception] = None) -> None:
        if exc:
            self._logger.error(f"{message}: {str(exc)}", exc_info=exc)
        else:
            self._logger.error(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def debug(self, message: str) -> None:
        self._logger.debug(message)


# Global logger instance
logger = Logger()