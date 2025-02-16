import logging
import os
import socket
from datetime import UTC, datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI color codes
COLORS = {
    "TRACE": "\033[35m",  # Magenta
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[41m",  # Red background
    "RESET": "\033[0m",  # Reset
}


class CustomFormatter(logging.Formatter):
    """Custom formatter that adds hostname, ISO timestamp and colors"""

    def format(self, record: logging.LogRecord) -> str:
        record.hostname = socket.gethostname()
        record.timestamp = datetime.now(UTC).isoformat()

        # Add colors to the log level
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"

        return super().format(record)


def setup_logger(name: str = "fastapi_app") -> logging.Logger:
    """Set up and configure logger with console handler"""
    # Get log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Initialize logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = CustomFormatter("%(timestamp)s - %(levelname)s - %(message)s")

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Create a default logger instance
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return setup_logger(name)
