"""
Logger module for the proxy server.

This module configures and provides the logging functionality for the proxy server.
"""

import logging
import sys
from datetime import datetime


def setup_logger(log_level='INFO'):
    """
    Set up and configure the logger for the proxy server.
    
    Args:
        log_level (str): The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
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
    
    return logger


def get_logger():
    """
    Get the proxy server logger instance.
    
    Returns:
        logging.Logger: The proxy server logger
    """
    return logging.getLogger('proxy_server') 