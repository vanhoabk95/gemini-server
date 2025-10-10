"""
Client handler module for the proxy server.

This module handles client connections and processes HTTP requests asynchronously.
"""

import asyncio

from proxy.logger import get_logger
from proxy.forwarder import forward_request
from proxy.gemini_handler import is_gemini_request, handle_gemini_request

logger = get_logger()

# Constants
BUFFER_SIZE = 8192
READ_TIMEOUT = 5  # seconds


async def handle_client(reader, writer):
    """
    Handle a client connection asynchronously.

    Args:
        reader (asyncio.StreamReader): The client stream reader
        writer (asyncio.StreamWriter): The client stream writer
    """
    client_address = writer.get_extra_info('peername')

    try:
        # Receive the client's HTTP request
        request_data = await _receive_request(reader)

        if not request_data:
            logger.warning(f"Empty request from {client_address[0]}")
            await _close_connection(writer)
            return

        # Check if this is a Gemini API request
        if is_gemini_request(request_data):
            success = await handle_gemini_request(writer, request_data, client_address)
        else:
            # Forward the request to the target server (normal HTTP/HTTPS proxy)
            success = await forward_request(reader, writer, request_data, client_address)

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
            writer.write(error_response)
            await writer.drain()

    except asyncio.TimeoutError:
        logger.warning(f"Client connection timed out: {client_address[0]}")
    except ConnectionResetError:
        logger.warning(f"Client connection reset: {client_address[0]}")
    except Exception as e:
        logger.error(f"Error handling client request: {e}")

    finally:
        await _close_connection(writer)


async def _receive_request(reader):
    """
    Receive the full HTTP request from the client.

    Args:
        reader (asyncio.StreamReader): The client stream reader

    Returns:
        bytes: The complete HTTP request
    """
    try:
        request_data = b''
        timeout_count = 0
        max_timeouts = 3  # Maximum number of consecutive timeouts before giving up

        while True:
            try:
                # Read with timeout
                data = await asyncio.wait_for(reader.read(BUFFER_SIZE), timeout=READ_TIMEOUT)
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

            except asyncio.TimeoutError:
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

    except asyncio.TimeoutError:
        logger.warning(f"Timeout receiving request")
        return None
    except Exception as e:
        logger.error(f"Error receiving request: {e}")
        return None


async def _close_connection(writer):
    """Close the client connection."""
    try:
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        logger.error(f"Error closing connection: {e}") 