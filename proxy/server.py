"""
Server module for the proxy server.

This module creates an async TCP server and handles incoming connections.
"""

import asyncio
import signal
import sys

from proxy.logger import get_logger
from proxy.handler import handle_client

logger = get_logger()


class ProxyServer:
    """
    Asynchronous proxy server that listens for incoming connections.
    """

    def __init__(self, config):
        """
        Initialize the proxy server.

        Args:
            config: Configuration object with host, port, and max_connections
        """
        self.host = config.host
        self.port = config.port
        self.max_connections = config.max_connections
        self.server = None
        self.running = False
        self.connection_count = 0
        self._last_connection_count = 0

        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    async def start(self):
        """Start the async proxy server."""
        try:
            # Create async server
            self.server = await asyncio.start_server(
                self._handle_connection,
                self.host,
                self.port,
                backlog=self.max_connections,
                reuse_address=True
            )

            self.running = True
            addr = self.server.sockets[0].getsockname()
            logger.info(f"Proxy server started on {addr[0]}:{addr[1]}")

            # Serve requests until Ctrl+C
            async with self.server:
                await self.server.serve_forever()

        except OSError as e:
            logger.error(f"Error starting proxy server: {e}")
            if e.errno == 98 or e.errno == 10048:  # Address already in use (Linux/Windows)
                logger.error(f"Port {self.port} is already in use")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error starting proxy server: {e}")
            sys.exit(1)

    async def _handle_connection(self, reader, writer):
        """Handle a new client connection."""
        self.connection_count += 1
        current_count = self.connection_count

        # Only log if count changed
        if self._last_connection_count != current_count:
            logger.debug(f"Active connections: {current_count}")
            self._last_connection_count = current_count

        try:
            await handle_client(reader, writer)
        finally:
            self.connection_count -= 1

    async def stop(self):
        """Stop the proxy server."""
        logger.info("Stopping proxy server...")
        self.running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("Proxy server stopped")

    def _signal_handler(self, sig, frame):
        """Handle signals to gracefully shut down the server."""
        logger.info(f"Received signal {sig}, shutting down...")

        # Create a task to stop the server
        if self.server:
            asyncio.create_task(self.stop())

        # Exit after a short delay
        logger.info("Shutting down gracefully...")
        sys.exit(0) 