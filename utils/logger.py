# ─────────────────────────────────────────────────────────────────────────────
# IRIS — Logging Utility
#
# WHY LOGGING?
# When something goes wrong in a live system — an API call fails, a model
# crashes, bad data sneaks through — you need a record of exactly what
# happened and when. Logs are your system's diary.
#
# Every module in IRIS calls get_logger(__name__) to get its own logger.
# All logs go to:
#   1. The terminal (so you can see what's happening live)
#   2. A log file (iris.log) so you have a permanent record
# ─────────────────────────────────────────────────────────────────────────────

import logging
import os
from datetime import datetime

# Create logs directory if it does not exist
os.makedirs("logs", exist_ok=True)

# Log file path — one log file per day
LOG_FILE = os.path.join("logs", f"iris_{datetime.now().strftime('%Y%m%d')}.log")


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a logger for a given module.

    INPUT:  name — typically __name__ from the calling module
    OUTPUT: configured Logger object

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
        logger.warning("Something suspicious happened")
        logger.error("Something went wrong")
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Format ────────────────────────────────────────────────────────────────
    # Example: 2024-11-15 14:32:01 | INFO     | data.ingestion | Fetching inflation...
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ── Terminal handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)   # Only INFO and above to terminal
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # ── File handler ──────────────────────────────────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)     # All levels to file
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger