#!/usr/bin/env python3
"""
Simple Python Proxy Server - Portable Version
"""

import sys
import asyncio
from proxy.logger import setup_logger
from proxy.server import ProxyServer
from proxy.request_stats import get_request_stats


class SimpleConfig:
    """Simple hardcoded configuration."""
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 80
        self.max_connections = 1000  # Async can handle much more than threading
        self.log_level = 'INFO'
        self.log_dir = 'logs'  # Directory for log files
        self.enable_file_logging = True  # Enable daily log rotation
        self.stats_dir = 'stats'  # Directory for request statistics
        self.stats_auto_save_interval = 60  # Auto-save stats every 60 seconds

    def __str__(self):
        return (f"Proxy Server Starting:\n"
                f"  Host: {self.host}\n"
                f"  Port: {self.port}\n"
                f"  Max Connections: {self.max_connections}")


async def async_main():
    """Async main entry point for the proxy server."""
    config = SimpleConfig()
    logger = setup_logger(
        log_level=config.log_level,
        log_dir=config.log_dir,
        enable_file_logging=config.enable_file_logging
    )

    logger.info(config)

    # Initialize request statistics tracking
    stats = await get_request_stats(
        stats_dir=config.stats_dir,
        auto_save_interval=config.stats_auto_save_interval
    )
    logger.info(f"Request statistics tracking enabled: {config.stats_dir}/")

    proxy_server = ProxyServer(config)

    try:
        await proxy_server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        await proxy_server.stop()
        await stats.stop()
    except Exception as e:
        logger.error(f"Error: {e}")
        await proxy_server.stop()
        await stats.stop()
        return 1

    return 0


def main():
    """Main entry point wrapper."""
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main()) 