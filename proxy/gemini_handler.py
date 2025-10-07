"""
Gemini API handler module.

This module handles requests to the Gemini API proxy.
"""

import re
import json
import socket
from urllib.parse import urlencode

from proxy.logger import get_logger
from proxy.gemini_config import get_gemini_config

logger = get_logger()


def is_gemini_request(request_data):
    """
    Check if the request is for Gemini API.

    Args:
        request_data (bytes): The raw HTTP request data

    Returns:
        bool: True if this is a Gemini API request
    """
    try:
        request_str = request_data.decode('utf-8', errors='replace')
        request_lines = request_str.split('\r\n')

        if not request_lines:
            return False

        # Parse request line
        parts = request_lines[0].split(' ', 2)
        if len(parts) < 2:
            return False

        method, path = parts[0], parts[1]

        # Check if path starts with /v1beta/ (Gemini API path)
        return path.startswith('/v1beta/')

    except Exception:
        return False


def handle_gemini_request(client_socket, request_data, client_address):
    """
    Handle a Gemini API request.

    Args:
        client_socket (socket.socket): The client socket
        request_data (bytes): The raw request data
        client_address (tuple): The client's address

    Returns:
        bool: True if successful, False otherwise
    """
    config = get_gemini_config()

    if not config.is_enabled():
        logger.warning(f"Gemini proxy request from {client_address[0]} but feature is disabled")
        error_response = _create_error_response(
            503,
            "Service Unavailable",
            "Gemini proxy is not enabled on this server"
        )
        client_socket.sendall(error_response)
        return False

    try:
        # Parse the request
        method, path, headers, body = _parse_gemini_request(request_data)

        if not path:
            logger.error(f"Could not parse Gemini request from {client_address[0]}")
            error_response = _create_error_response(400, "Bad Request", "Invalid request format")
            client_socket.sendall(error_response)
            return False

        logger.info(f"Gemini API request from {client_address[0]}: {method} {path}")

        # Replace model in path with configured model
        path = _replace_model_in_path(path, config.get_model())

        # Forward to Google API
        response_data = _forward_to_google(method, path, headers, body, config)

        if response_data:
            # Send response back to client
            client_socket.sendall(response_data)
            return True
        else:
            error_response = _create_error_response(502, "Bad Gateway", "Failed to reach Google API")
            client_socket.sendall(error_response)
            return False

    except Exception as e:
        logger.error(f"Error handling Gemini request: {e}")
        error_response = _create_error_response(500, "Internal Server Error", str(e))
        client_socket.sendall(error_response)
        return False


def _parse_gemini_request(request_data):
    """
    Parse a Gemini API request.

    Args:
        request_data (bytes): The raw request data

    Returns:
        tuple: (method, path, headers, body)
    """
    try:
        request_str = request_data.decode('utf-8', errors='replace')
        request_lines = request_str.split('\r\n')

        # Parse request line
        method, path, _ = request_lines[0].split(' ', 2)

        # Parse headers
        headers = {}
        body_start = 0
        for i, line in enumerate(request_lines[1:], 1):
            if not line:
                body_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()

        # Get body if present
        body = b''
        if body_start > 0:
            body_lines = request_lines[body_start:]
            body = '\r\n'.join(body_lines).encode('utf-8')

        return method, path, headers, body

    except Exception as e:
        logger.error(f"Error parsing Gemini request: {e}")
        return None, None, None, None


def _replace_model_in_path(path, target_model):
    """
    Replace model name in the path with target model.

    Args:
        path (str): Original path
        target_model (str): Target model name

    Returns:
        str: Path with replaced model
    """
    # Pattern: models/any-model-name:action
    pattern = r'models/[^:/]+:'
    replacement = f'models/{target_model}:'

    new_path = re.sub(pattern, replacement, path)

    if new_path != path:
        logger.debug(f"Replaced model in path: {path} -> {new_path}")

    return new_path


def _forward_to_google(method, path, headers, body, config):
    """
    Forward the request to Google API with automatic failover.

    Args:
        method (str): HTTP method
        path (str): API path
        headers (dict): Request headers
        body (bytes): Request body
        config (GeminiConfig): Configuration object

    Returns:
        bytes: The complete HTTP response or None on error
    """
    try:
        # Import httpx here to avoid requiring it if Gemini is disabled
        import httpx
    except ImportError:
        logger.error("httpx library not found. Please install: pip install httpx")
        return None

    # Remember starting config index for failover
    start_index = config.get_current_index()

    # Try with current config and failover to next if needed
    while True:
        try:
            # Build full URL
            url = f"{config.get_api_base()}{path}"

            # Add API key as query parameter
            if '?' in url:
                url += f"&key={config.get_api_key()}"
            else:
                url += f"?key={config.get_api_key()}"

            # Prepare headers
            request_headers = {
                'Content-Type': headers.get('Content-Type', 'application/json'),
                'User-Agent': headers.get('User-Agent', 'Python-Proxy/1.0')
            }

            # Make synchronous request with httpx
            with httpx.Client(timeout=60.0) as client:
                if method == 'POST':
                    response = client.post(url, content=body, headers=request_headers)
                elif method == 'GET':
                    response = client.get(url, headers=request_headers)
                else:
                    logger.warning(f"Unsupported method for Gemini: {method}")
                    return None

                # Check if request was successful
                if response.status_code < 500:
                    # Success or client error (4xx) - don't retry
                    response_data = _build_http_response(
                        response.status_code,
                        response.reason_phrase,
                        response.headers,
                        response.content
                    )
                    logger.debug(f"Google API response: {response.status_code} - {len(response.content)} bytes")
                    return response_data
                else:
                    # Server error (5xx) - try next config
                    logger.warning(f"Google API error {response.status_code}, trying next config")
                    raise Exception(f"Server error: {response.status_code}")

        except Exception as e:
            logger.warning(f"Error with config #{config.get_current_index() + 1}: {e}")

            # Try to move to next config
            if not config.try_next_config(start_index):
                # We've tried all configs
                logger.error("All Gemini configs failed")
                return None

            logger.info(f"Trying Gemini config #{config.get_current_index() + 1}")
            # Continue loop with new config


def _build_http_response(status_code, reason, headers, body):
    """
    Build a complete HTTP response.

    Args:
        status_code (int): HTTP status code
        reason (str): Status reason phrase
        headers (dict): Response headers
        body (bytes): Response body

    Returns:
        bytes: Complete HTTP response
    """
    # Status line
    response = f"HTTP/1.1 {status_code} {reason}\r\n".encode('utf-8')

    # Headers
    for key, value in headers.items():
        # Skip certain headers
        if key.lower() in ['transfer-encoding', 'connection']:
            continue
        response += f"{key}: {value}\r\n".encode('utf-8')

    # Add connection close header
    response += b"Connection: close\r\n"

    # End of headers
    response += b"\r\n"

    # Body
    response += body

    return response


def _create_error_response(status_code, reason, message):
    """
    Create an error HTTP response.

    Args:
        status_code (int): HTTP status code
        reason (str): Status reason phrase
        message (str): Error message

    Returns:
        bytes: Complete HTTP error response
    """
    error_body = {
        "error": {
            "code": status_code,
            "message": message,
            "status": reason
        }
    }

    body = json.dumps(error_body).encode('utf-8')

    response = f"HTTP/1.1 {status_code} {reason}\r\n".encode('utf-8')
    response += b"Content-Type: application/json\r\n"
    response += f"Content-Length: {len(body)}\r\n".encode('utf-8')
    response += b"Connection: close\r\n"
    response += b"\r\n"
    response += body

    return response
