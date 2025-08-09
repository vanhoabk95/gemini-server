#!/usr/bin/env python3
"""
Simple Python Proxy Server

A lightweight HTTP proxy server implemented in Python using only standard libraries.
"""

import sys

from proxy.config import get_config
from proxy.logger import setup_logger
from proxy.server import ProxyServer


def main():
    """Main entry point for the proxy server."""
    # Parse command-line arguments
    config = get_config()
    
    # Set up the logger
    logger = setup_logger(config.log_level)
    
    # Log configuration
    logger.info(config)
    
    # Create and start the proxy server
    proxy_server = ProxyServer(config)
    
    try:
        proxy_server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected")
        proxy_server.stop()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        proxy_server.stop()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 