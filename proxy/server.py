"""
Server module for the proxy server.

This module creates a TCP socket, binds to the LAN interface, and listens for
incoming connections.
"""

import socket
import threading
import signal
import sys

from proxy.logger import get_logger
from proxy.handler import ClientHandler

logger = get_logger()


class ProxyServer:
    """
    Proxy server that listens for incoming connections and dispatches them to
    client handlers.
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
        self.server_socket = None
        self.running = False
        self.connections = []
        self._last_connection_count = 0
        
        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """Start the proxy server."""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Allow reuse of the socket address
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to host and port
            self.server_socket.bind((self.host, self.port))
            
            # Listen for connections (queuing up to max_connections)
            self.server_socket.listen(self.max_connections)
            
            self.running = True
            logger.info(f"Proxy server started on {self.host}:{self.port}")
            
            # Main server loop
            self._accept_connections()
            
        except OSError as e:
            logger.error(f"Error starting proxy server: {e}")
            if e.errno == 98:  # Address already in use
                logger.error(f"Port {self.port} is already in use")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error starting proxy server: {e}")
            sys.exit(1)
    
    def _accept_connections(self):
        """Accept incoming connections and dispatch them to client handlers."""
        while self.running:
            try:
                # Set a timeout on the accept call to prevent blocking indefinitely
                self.server_socket.settimeout(1.0)  # 1 second timeout
                
                # Accept client connection
                client_socket, client_address = self.server_socket.accept()
                
                # Reset socket to blocking mode for the client handler
                client_socket.settimeout(None)
                
                # Create and start a new client handler thread
                handler = ClientHandler(client_socket, client_address)
                handler.daemon = True  # Allow the server to exit even if threads are running
                handler.start()
                
                # Keep track of active connections
                self.connections.append(handler)
                
                # Clean up completed threads
                self.connections = [conn for conn in self.connections if conn.is_alive()]
                
                # Only log active connections if there's been a change in count
                active_connections = len(self.connections)
                if hasattr(self, '_last_connection_count') and self._last_connection_count != active_connections:
                    logger.debug(f"Active connections: {active_connections}")
                self._last_connection_count = active_connections
                
            except KeyboardInterrupt:
                self.stop()
                break
            except socket.timeout:
                # This is expected behavior with the timeout we set, no need to log it
                continue
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                if not self.running:
                    break
    
    def stop(self):
        """Stop the proxy server."""
        logger.info("Stopping proxy server...")
        self.running = False
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Wait for all client handlers to finish
        for conn in self.connections:
            if conn.is_alive():
                conn.join(1.0)  # Wait up to 1 second for each thread
        
        logger.info("Proxy server stopped")
    
    def _signal_handler(self, sig, frame):
        """Handle signals to gracefully shut down the server."""
        logger.info(f"Received signal {sig}, shutting down...")
        
        # Instead of exiting immediately, just stop the server
        # This gives active connections a chance to complete
        self.stop()
        
        # Only exit if there are no active connections
        active_connections = len([conn for conn in self.connections if conn.is_alive()])
        if active_connections == 0:
            logger.info("No active connections, exiting...")
            sys.exit(0)
        else:
            logger.info(f"Waiting for {active_connections} active connections to complete...")
            # Don't exit, allow the server to continue with active connections 