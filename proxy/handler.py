"""
Client handler module for the proxy server.

This module handles client connections and processes HTTP requests in separate
threads.
"""

import socket
import threading
import select

from proxy.logger import get_logger
from proxy.forwarder import forward_request

logger = get_logger()

# Constants
BUFFER_SIZE = 8192
READ_TIMEOUT = 5  # seconds


class ClientHandler(threading.Thread):
    """
    Handler for client connections.
    
    Processes client requests in a separate thread.
    """
    
    def __init__(self, client_socket, client_address):
        """
        Initialize a new client handler.
        
        Args:
            client_socket (socket.socket): The client socket
            client_address (tuple): The client's address (ip, port)
        """
        super().__init__()
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_socket.settimeout(READ_TIMEOUT)
        # Only log new connections at trace level (which we don't use), effectively disabling this very verbose log
        # Uncomment if needed for debugging specific issues
        # logger.debug(f"New client connection from {client_address[0]}:{client_address[1]}")
    
    def run(self):
        """Handle the client request."""
        try:
            # Receive the client's HTTP request
            request_data = self._receive_request()
            
            if not request_data:
                logger.warning(f"Empty request from {self.client_address[0]}")
                self._close_connection()
                return
            
            # Forward the request to the target server
            success = forward_request(self.client_socket, request_data, self.client_address)
            
            if not success:
                # Send error response to the client
                error_response = (
                    b"HTTP/1.1 502 Bad Gateway\r\n"
                    b"Content-Type: text/html\r\n"
                    b"Connection: close\r\n"
                    b"\r\n"
                    b"<html><body><h1>502 Bad Gateway</h1>"
                    b"<p>The proxy server could not handle the request.</p>"
                    b"</body></html>"
                )
                self.client_socket.sendall(error_response)
        
        except socket.timeout:
            logger.warning(f"Client connection timed out: {self.client_address[0]}")
        except ConnectionResetError:
            logger.warning(f"Client connection reset: {self.client_address[0]}")
        except Exception as e:
            logger.error(f"Error handling client request: {e}")
        
        finally:
            self._close_connection()
    
    def _receive_request(self):
        """
        Receive the full HTTP request from the client.
        
        Returns:
            bytes: The complete HTTP request
        """
        try:
            request_data = b''
            timeout_count = 0
            max_timeouts = 3  # Maximum number of consecutive timeouts before giving up
            
            while True:
                try:
                    data = self.client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    
                    # Reset timeout counter on successful data reception
                    timeout_count = 0
                    request_data += data
                    
                    # Check if we've received a complete HTTP request
                    if b'\r\n\r\n' in request_data:
                        # Request headers are complete
                        # Check if it's a CONNECT method (no need to wait for body)
                        if request_data.startswith(b'CONNECT '):
                            break
                        
                        # For other methods, check if we need to receive a body
                        if b'Content-Length: ' in request_data:
                            # Extract Content-Length value
                            content_length_start = request_data.find(b'Content-Length: ') + 16
                            content_length_end = request_data.find(b'\r\n', content_length_start)
                            content_length = int(request_data[content_length_start:content_length_end].strip())
                            
                            # Calculate the header length
                            header_end = request_data.find(b'\r\n\r\n') + 4
                            
                            # Check if we've received the full body
                            if len(request_data) - header_end >= content_length:
                                break
                        else:
                            # No Content-Length header, assume no body
                            break
                
                except socket.timeout:
                    # Increment timeout counter
                    timeout_count += 1
                    logger.debug(f"Socket read timeout ({timeout_count}/{max_timeouts})")
                    
                    # If we've hit max timeouts, abort reception
                    if timeout_count >= max_timeouts:
                        logger.warning(f"Maximum read timeouts reached, aborting request reception")
                        break
                    
                    # If we have partial headers, check if they might be complete
                    if b'\r\n\r\n' in request_data:
                        logger.debug("Partial headers received, proceeding with request")
                        break
                    
                    # Continue trying to receive data
                    continue
            
            return request_data
            
        except socket.timeout:
            logger.warning(f"Timeout receiving request from {self.client_address[0]}")
            return None
        except Exception as e:
            logger.error(f"Error receiving request: {e}")
            return None
    
    def _close_connection(self):
        """Close the client connection."""
        try:
            self.client_socket.close()
            # This is too verbose for regular logging - only uncomment if needed for debugging
            # logger.debug(f"Closed connection to {self.client_address[0]}")
        except Exception as e:
            logger.error(f"Error closing connection: {e}") 