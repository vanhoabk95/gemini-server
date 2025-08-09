#!/usr/bin/env python3
"""
Simple Python Proxy Server - Portable Version
"""

import sys
from proxy.logger import setup_logger
from proxy.server import ProxyServer


class SimpleConfig:
    """Simple hardcoded configuration."""
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 80
        self.max_connections = 150
        self.log_level = 'INFO'
    
    def __str__(self):
        return (f"Proxy Server Starting:\n"
                f"  Host: {self.host}\n"
                f"  Port: {self.port}\n"
                f"  Max Connections: {self.max_connections}")


def main():
    """Main entry point for the proxy server."""
    config = SimpleConfig()
    logger = setup_logger(config.log_level)
    
    logger.info(config)
    
    proxy_server = ProxyServer(config)
    
    try:
        proxy_server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        proxy_server.stop()
    except Exception as e:
        logger.error(f"Error: {e}")
        proxy_server.stop()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 