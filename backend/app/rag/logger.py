"""One logger per pipeline run. Writes to stdout and to
outputs/logs/run-<stage>-<timestamp>.log so runs can be committed as evidence."""
import logging
import sys
from datetime import datetime
from .config import LOG_DIR


def get_logger(stage: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOG_DIR / f"run-{stage}-{ts}.log"

    logger = logging.getLogger(f"rag.{stage}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    for h in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_path)):
        h.setFormatter(fmt)
        logger.addHandler(h)

    logger.info("log file: %s", log_path)
    return logger
