"""
Forwarding module for the proxy server.

This module handles establishing connections to target servers, forwarding
requests, and relaying responses back to clients.
"""

import socket
import select
from urllib.parse import urlparse
import time
import logging

from proxy.logger import get_logger

logger = get_logger()

# Constants
BUFFER_SIZE = 8192
CONNECTION_TIMEOUT = 10  # seconds


def parse_request(request_data):
    """
    Parse the HTTP request to extract method, URL and host.
    
    Args:
        request_data (bytes): The raw HTTP request data
        
    Returns:
        tuple: (method, url, host, port, path, headers)
    """
    try:
        # Decode request to string and split into lines
        request_lines = request_data.decode('utf-8', errors='replace').split('\r\n')
        
        # Parse the request line (e.g., "GET http://example.com/ HTTP/1.1")
        method, url, version = request_lines[0].split(' ', 2)
        
        # Extract host from the headers
        host = None
        port = 80  # Default HTTP port
        if method == 'CONNECT':
            # For CONNECT method, the URL is hostname:port
            host_port = url.split(':', 1)
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443
            path = ''
        else:
            # Regular HTTP request
            headers = {}
            
            for line in request_lines[1:]:
                if not line:
                    break
                    
                # Parse headers
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
                    
                    # Extract host from Host header
                    if key.strip().lower() == 'host':
                        host_parts = value.strip().split(':', 1)
                        host = host_parts[0]
                        if len(host_parts) > 1:
                            port = int(host_parts[1])
            
            # If URL is absolute, parse it to extract host, port, and path
            if url.startswith('http'):
                parsed_url = urlparse(url)
                host = parsed_url.hostname or host
                port = parsed_url.port or port
                path = parsed_url.path
                if parsed_url.query:
                    path += '?' + parsed_url.query
            else:
                # Relative URL
                path = url
            
            return method, url, host, port, path, headers
        
        return method, url, host, port, path, {} if method == 'CONNECT' else headers
        
    except Exception as e:
        logger.error(f"Error parsing request: {e}")
        return None, None, None, None, None, None


def create_https_tunnel(client_socket, host, port, client_address):
    """
    Create an HTTPS tunnel for CONNECT requests.
    
    Args:
        client_socket (socket.socket): The client socket
        host (str): The target host
        port (int): The target port
        client_address (tuple): The client's address (ip, port)
        
    Returns:
        bool: True if tunneling was successful, False otherwise
    """
    try:
        # Log the CONNECT request
        logger.info(f"HTTPS CONNECT request from {client_address[0]} to {host}:{port}")
        
        # Create a socket to connect to the target server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(CONNECTION_TIMEOUT)
        
        # Connect to the target server
        server_socket.connect((host, port))
        
        # Send a 200 Connection Established response to the client
        success_response = b"HTTP/1.1 200 Connection Established\r\n\r\n"
        client_socket.sendall(success_response)
        
        # Set up bidirectional communication
        tunnel_active = True
        client_socket.setblocking(False)
        server_socket.setblocking(False)
        
        while tunnel_active:
            # Lists of sockets we want to read from and write to
            read_sockets = [client_socket, server_socket]
            write_sockets = []
            error_sockets = [client_socket, server_socket]
            
            try:
                # Use select to wait for data on any socket
                # Reduce the timeout to 0.5 seconds to prevent long blocking
                readable, writable, errored = select.select(read_sockets, write_sockets, error_sockets, 0.5)
                
                # No activity detected during the timeout period
                if not readable and not writable and not errored:
                    # Add a brief sleep to avoid high CPU usage in case of continuous timeouts
                    time.sleep(0.01)
                    continue
                
                # Check for data from client
                if client_socket in readable:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data:
                        tunnel_active = False
                        break
                    server_socket.sendall(data)
                
                # Check for data from server
                if server_socket in readable:
                    data = server_socket.recv(BUFFER_SIZE)
                    if not data:
                        tunnel_active = False
                        break
                    client_socket.sendall(data)
                
                # Check for errors
                if client_socket in errored or server_socket in errored:
                    tunnel_active = False
                    break
                    
            except socket.error:
                tunnel_active = False
                break
        
        server_socket.close()
        # This message is too verbose for normal operation - commented out to reduce log spam
        # logger.debug(f"HTTPS tunnel to {host}:{port} closed")
        return True
        
    except socket.gaierror:
        logger.error(f"Could not resolve hostname: {host}")
        error_response = b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n"
        client_socket.sendall(error_response)
        return False
    except socket.timeout:
        logger.error(f"Connection timeout to {host}:{port}")
        error_response = b"HTTP/1.1 504 Gateway Timeout\r\nContent-Length: 0\r\n\r\n"
        client_socket.sendall(error_response)
        return False
    except ConnectionRefusedError:
        logger.error(f"Connection refused by {host}:{port}")
        error_response = b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n"
        client_socket.sendall(error_response)
        return False
    except Exception as e:
        logger.error(f"Error creating HTTPS tunnel to {host}:{port}: {e}")
        error_response = b"HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
        client_socket.sendall(error_response)
        return False


def forward_request(client_socket, request_data, client_address):
    """
    Forward the client's request to the target server and relay the response.
    
    Args:
        client_socket (socket.socket): The client socket
        request_data (bytes): The raw request data from the client
        client_address (tuple): The client's address (ip, port)
        
    Returns:
        bool: True if the forwarding was successful, False otherwise
    """
    method, url, host, port, path, headers = parse_request(request_data)
    
    if not host:
        logger.error(f"Could not determine host from request: {request_data[:100]}")
        return False
    
    # Detect and prevent proxy loops - check if the request is to the proxy itself
    # Check if the target host matches the client's IP (indicating a potential loop)
    if host == client_address[0]:
        logger.warning(f"Detected potential proxy loop: request from {client_address[0]} to itself ({host}:{port})")
        error_response = b"HTTP/1.1 508 Loop Detected\r\nContent-Type: text/html\r\nContent-Length: 108\r\n\r\n"
        error_response += b"<html><body><h1>508 Loop Detected</h1><p>Request blocked to prevent a proxy loop.</p></body></html>"
        client_socket.sendall(error_response)
        return False
    
    # Handle CONNECT method for HTTPS
    if method == 'CONNECT':
        return create_https_tunnel(client_socket, host, port, client_address)
    
    # Regular HTTP request
    logger.info(f"Request from {client_address[0]}: {method} {host}:{port}{path}")
    
    try:
        # Connect to the target server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.settimeout(CONNECTION_TIMEOUT)
        server_socket.connect((host, port))
        
        # Send the original request to the target server
        server_socket.sendall(request_data)
        
        # Receive the response from the target server
        response_data = b''
        while True:
            try:
                data = server_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                response_data += data
                # Forward the data to the client immediately
                client_socket.sendall(data)
            except socket.timeout:
                break
        
        # Log details at appropriate level (INFO for requests, DEBUG for response size)
        
        # Reduce verbosity by making this debug-level response size log conditional on log level
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Response from {host}:{port} - Size: {len(response_data)} bytes")
        server_socket.close()
        return True
        
    except socket.gaierror:
        logger.error(f"Could not resolve hostname: {host}")
        return False
    except socket.timeout:
        logger.error(f"Connection timeout to {host}:{port}")
        return False
    except ConnectionRefusedError:
        logger.error(f"Connection refused by {host}:{port}")
        return False
    except Exception as e:
        logger.error(f"Error forwarding request to {host}:{port}: {e}")
        return False