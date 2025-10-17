from __future__ import annotations

import logging
import os
from typing import Optional

_LOGGING_CONFIGURED = False


def _configure_logging(level: Optional[str]) -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_logging(None)
    return logging.getLogger(name)
