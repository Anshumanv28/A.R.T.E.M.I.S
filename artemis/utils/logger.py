"""
Centralized logging configuration for A.R.T.E.M.I.S.

Provides structured logging with configurable levels, file output,
and proper error tracking throughout the codebase.
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Try to import colorama for colored console output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)  # Auto-reset colors after each print
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Define dummy color constants if colorama not available
    class Fore:
        RED = ""
        YELLOW = ""
        GREEN = ""
        BLUE = ""
        CYAN = ""
        MAGENTA = ""
        RESET = ""
    class Style:
        RESET_ALL = ""

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Log directory in user home
LOG_DIR = Path.home() / ".artemis" / "logs"
LOG_FILE = LOG_DIR / "artemis.log"

# Maximum log file size (10MB)
MAX_LOG_SIZE = 10 * 1024 * 1024

# Number of backup log files to keep
BACKUP_COUNT = 5

# Track if logging has been configured
_logging_configured = False


def _get_log_level() -> int:
    """
    Get log level from environment variable or use default.
    
    Returns:
        Logging level constant (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level_str = os.getenv("ARTEMIS_LOG_LEVEL", "INFO").upper()
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    return level_map.get(log_level_str, DEFAULT_LOG_LEVEL)


def _create_log_directory() -> None:
    """Create log directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # Color mapping for different log levels
    COLORS = {
        logging.DEBUG: Fore.CYAN if COLORAMA_AVAILABLE else "",
        logging.INFO: Fore.GREEN if COLORAMA_AVAILABLE else "",
        logging.WARNING: Fore.YELLOW if COLORAMA_AVAILABLE else "",
        logging.ERROR: Fore.RED if COLORAMA_AVAILABLE else "",
        logging.CRITICAL: Fore.RED + Style.BRIGHT if COLORAMA_AVAILABLE else "",
    }
    
    RESET = Style.RESET_ALL if COLORAMA_AVAILABLE else ""
    
    def format(self, record):
        # Add color to levelname
        if COLORAMA_AVAILABLE:
            levelname = record.levelname
            color = self.COLORS.get(record.levelno, "")
            record.levelname = f"{color}{levelname}{self.RESET}"
        
        # Format the message
        return super().format(record)


def _setup_console_handler(logger: logging.Logger, log_level: int) -> None:
    """
    Set up console handler for development output with colored output.
    
    Args:
        logger: Logger instance to add handler to
        log_level: Logging level for console output
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use colored formatter for console (more readable)
    console_format = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)


def _setup_file_handler(logger: logging.Logger, log_level: int) -> None:
    """
    Set up rotating file handler for persistent logging.
    
    Args:
        logger: Logger instance to add handler to
        log_level: Logging level for file output
    """
    _create_log_directory()
    
    file_handler = RotatingFileHandler(
        str(LOG_FILE),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    
    # Detailed format for file logging
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)


def setup_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    This function configures logging for the entire application on first call,
    then returns a logger instance for the specified module.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        log_level: Optional log level override. If None, uses environment variable or default.
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
    """
    global _logging_configured
    
    logger = logging.getLogger(name)
    
    # Configure root logger only once
    if not _logging_configured:
        root_logger = logging.getLogger("artemis")
        root_log_level = log_level if log_level is not None else _get_log_level()
        root_logger.setLevel(root_log_level)
        
        # Remove any existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Set up handlers
        _setup_console_handler(root_logger, root_log_level)
        _setup_file_handler(root_logger, root_log_level)
        
        # Prevent propagation to root logger to avoid duplicate messages
        root_logger.propagate = False
        
        _logging_configured = True
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Convenience function that calls setup_logger. Use this in your modules
    to get a properly configured logger.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> from artemis.utils import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return setup_logger(name)

