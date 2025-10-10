"""
Forwarding module for the proxy server.

This module handles establishing connections to target servers, forwarding
requests, and relaying responses back to clients asynchronously.
"""

import asyncio
from urllib.parse import urlparse
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


async def create_https_tunnel(client_reader, client_writer, host, port, client_address):
    """
    Create an HTTPS tunnel for CONNECT requests.

    Args:
        client_reader (asyncio.StreamReader): The client stream reader
        client_writer (asyncio.StreamWriter): The client stream writer
        host (str): The target host
        port (int): The target port
        client_address (tuple): The client's address (ip, port)

    Returns:
        bool: True if tunneling was successful, False otherwise
    """
    try:
        # Log the CONNECT request
        logger.info(f"HTTPS CONNECT request from {client_address[0]} to {host}:{port}")

        # Connect to the target server
        server_reader, server_writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=CONNECTION_TIMEOUT
        )

        # Send a 200 Connection Established response to the client
        success_response = b"HTTP/1.1 200 Connection Established\r\n\r\n"
        client_writer.write(success_response)
        await client_writer.drain()

        # Set up bidirectional communication
        async def pipe(reader, writer):
            try:
                while True:
                    data = await reader.read(BUFFER_SIZE)
                    if not data:
                        break
                    writer.write(data)
                    await writer.drain()
            except Exception:
                pass
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        # Run both directions concurrently
        await asyncio.gather(
            pipe(client_reader, server_writer),
            pipe(server_reader, client_writer),
            return_exceptions=True
        )

        return True

    except asyncio.TimeoutError:
        logger.error(f"Connection timeout to {host}:{port}")
        error_response = b"HTTP/1.1 504 Gateway Timeout\r\nContent-Length: 0\r\n\r\n"
        client_writer.write(error_response)
        await client_writer.drain()
        return False
    except ConnectionRefusedError:
        logger.error(f"Connection refused by {host}:{port}")
        error_response = b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n"
        client_writer.write(error_response)
        await client_writer.drain()
        return False
    except OSError as e:
        logger.error(f"Could not resolve hostname: {host}")
        error_response = b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n"
        client_writer.write(error_response)
        await client_writer.drain()
        return False
    except Exception as e:
        logger.error(f"Error creating HTTPS tunnel to {host}:{port}: {e}")
        error_response = b"HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n"
        client_writer.write(error_response)
        await client_writer.drain()
        return False


async def forward_request(client_reader, client_writer, request_data, client_address):
    """
    Forward the client's request to the target server and relay the response.

    Args:
        client_reader (asyncio.StreamReader): The client stream reader
        client_writer (asyncio.StreamWriter): The client stream writer
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
        client_writer.write(error_response)
        await client_writer.drain()
        return False

    # Handle CONNECT method for HTTPS
    if method == 'CONNECT':
        return await create_https_tunnel(client_reader, client_writer, host, port, client_address)

    # Regular HTTP request
    logger.info(f"Request from {client_address[0]}: {method} {host}:{port}{path}")

    try:
        # Connect to the target server
        server_reader, server_writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=CONNECTION_TIMEOUT
        )

        # Send the original request to the target server
        server_writer.write(request_data)
        await server_writer.drain()

        # Receive the response from the target server
        response_data = b''
        while True:
            try:
                data = await asyncio.wait_for(server_reader.read(BUFFER_SIZE), timeout=CONNECTION_TIMEOUT)
                if not data:
                    break
                response_data += data
                # Forward the data to the client immediately
                client_writer.write(data)
                await client_writer.drain()
            except asyncio.TimeoutError:
                break

        # Reduce verbosity by making this debug-level response size log conditional on log level
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Response from {host}:{port} - Size: {len(response_data)} bytes")

        server_writer.close()
        await server_writer.wait_closed()
        return True

    except asyncio.TimeoutError:
        logger.error(f"Connection timeout to {host}:{port}")
        return False
    except ConnectionRefusedError:
        logger.error(f"Connection refused by {host}:{port}")
        return False
    except OSError as e:
        logger.error(f"Could not resolve hostname: {host}")
        return False
    except Exception as e:
        logger.error(f"Error forwarding request to {host}:{port}: {e}")
        return False