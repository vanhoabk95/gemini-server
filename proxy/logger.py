"""
Logger module for the proxy server.

This module configures and provides the logging functionality for the proxy server.
"""

import logging
import sys
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


def setup_logger(log_level='INFO', log_dir='logs', enable_file_logging=True):
    """
    Set up and configure the logger for the proxy server.

    Args:
        log_level (str): The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir (str): Directory to store log files
        enable_file_logging (bool): Whether to enable file logging

    Returns:
        logging.Logger: The configured logger instance
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Create logger
    logger = logging.getLogger('proxy_server')
    logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler and set level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Add formatter to console handler
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Add file handler with daily rotation
    if enable_file_logging:
        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # File handler with daily rotation
        log_file = os.path.join(log_dir, 'proxy_server.log')
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',      # Rotate at midnight
            interval=1,           # Every 1 day
            backupCount=30,       # Keep 30 days of logs
            encoding='utf-8',
            utc=False             # Use local time
        )
        file_handler.setLevel(numeric_level)

        # Set filename suffix with date
        file_handler.suffix = '%Y-%m-%d'

        # Add formatter to file handler
        file_handler.setFormatter(formatter)

        # Add file handler to logger
        logger.addHandler(file_handler)

        logger.info(f"File logging enabled: {log_file} (daily rotation, keep 30 days)")

    return logger


def get_logger():
    """
    Get the proxy server logger instance.
    
    Returns:
        logging.Logger: The proxy server logger
    """
    return logging.getLogger('proxy_server') 