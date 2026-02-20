"""Elden Ring themed logging for glintstone preprocessing."""
import logging
import sys


class GlintstoneFormatter(logging.Formatter):
    """Custom formatter with Elden Ring themed prefixes."""

    FORMATS = {
        logging.DEBUG: "Consulting the stars: %(message)s",
        logging.INFO: "[*] %(message)s",
        logging.WARNING: "The Two Fingers warn: %(message)s",
        logging.ERROR: "YOU DIED: %(message)s",
        logging.CRITICAL: "YOU DIED: %(message)s",
    }

    def format(self, record):
        fmt = self.FORMATS.get(record.levelno, "[*] %(message)s")
        formatter = logging.Formatter(fmt)
        return formatter.format(record)


def get_logger(name="glintstone", verbose=False):
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(GlintstoneFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    return logger
