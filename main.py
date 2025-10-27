#!/usr/bin/env python3
"""
Simple Python Proxy Server - Portable Version
"""

import sys
import json
import asyncio
from pathlib import Path
from proxy.logger import setup_logger
from proxy.server import ProxyServer
from proxy.request_stats import get_request_stats


class SimpleConfig:
    """Configuration loaded from proxy_config.json."""

    CONFIG_FILE = 'proxy_config.json'

    # Default values
    DEFAULTS = {
        'host': '0.0.0.0',
        'port': 80,
        'max_connections': 1000,
        'log_level': 'INFO',
        'log_dir': 'logs',
        'enable_file_logging': True,
        'stats_dir': 'stats',
        'stats_auto_save_interval': 60
    }

    def __init__(self, config_file=None):
        """Load configuration from JSON file."""
        config_path = Path(config_file or self.CONFIG_FILE)

        # Load from file or use defaults
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                print(f"Configuration loaded from {config_path}")
            except Exception as e:
                print(f"Error loading config file: {e}, using defaults")
                config_data = {}
        else:
            print(f"Config file not found, creating {config_path} with defaults")
            config_data = self.DEFAULTS
            # Create default config file
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.DEFAULTS, f, indent=2)
            except Exception as e:
                print(f"Error creating config file: {e}")

        # Set attributes with defaults as fallback
        self.host = config_data.get('host', self.DEFAULTS['host'])
        self.port = config_data.get('port', self.DEFAULTS['port'])
        self.max_connections = config_data.get('max_connections', self.DEFAULTS['max_connections'])
        self.log_level = config_data.get('log_level', self.DEFAULTS['log_level'])
        self.log_dir = config_data.get('log_dir', self.DEFAULTS['log_dir'])
        self.enable_file_logging = config_data.get('enable_file_logging', self.DEFAULTS['enable_file_logging'])
        self.stats_dir = config_data.get('stats_dir', self.DEFAULTS['stats_dir'])
        self.stats_auto_save_interval = config_data.get('stats_auto_save_interval', self.DEFAULTS['stats_auto_save_interval'])

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