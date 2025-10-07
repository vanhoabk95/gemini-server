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
            400,
            "Bad Request",
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
        logger.debug(f"Request headers: {headers}")

        # Log request body for debugging
        if body:
            try:
                body_json = json.loads(body.decode('utf-8', errors='replace'))
                logger.info(f"Request body: {json.dumps(body_json, indent=2)}")
            except:
                logger.debug(f"Request body (raw, first 500 chars): {body[:500]}")

        # Replace model in path with configured model
        original_path = path
        path = _replace_model_in_path(path, config.get_model())
        if original_path != path:
            logger.info(f"Model replacement: {original_path} -> {path}")
        else:
            logger.debug(f"No model replacement needed for path: {path}")

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
    max_retries = config.get_config_count()
    retry_count = 0

    # Try with current config and failover to next if needed
    while retry_count < max_retries:
        try:
            # Get current config details
            current_config = config.get_current_config()
            api_key = config.get_api_key()
            model = config.get_model()
            api_base = config.get_api_base()

            # Mask API key for logging
            masked_key = f"***{api_key[-4:]}" if api_key and len(api_key) > 4 else "***"

            # Log which config we're using
            logger.info(f"Using config #{config.get_current_index() + 1}: model={model}, api_key={masked_key}")

            # Build full URL
            url = f"{api_base}{path}"

            # Add API key as query parameter
            if '?' in url:
                url += f"&key={api_key}"
            else:
                url += f"?key={api_key}"

            # Prepare headers
            request_headers = {
                'Content-Type': headers.get('Content-Type', 'application/json'),
                'User-Agent': headers.get('User-Agent', 'Python-Proxy/1.0')
            }

            # Log what we're sending to Google (mask API key in URL)
            safe_url = url.replace(api_key, masked_key)
            logger.debug(f"Forwarding to URL: {safe_url}")
            logger.debug(f"Request headers to Google: {request_headers}")
            if body:
                try:
                    body_json = json.loads(body.decode('utf-8', errors='replace'))
                    logger.debug(f"Request body to Google: {json.dumps(body_json, indent=2)}")
                except:
                    logger.debug(f"Request body to Google (raw): {body[:200]}")

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
                if response.status_code == 200:
                    # Success
                    logger.info(f"Google API response: {response.status_code} - {len(response.content)} bytes")
                    response_data = _build_http_response(
                        response.status_code,
                        response.reason_phrase,
                        response.headers,
                        response.content
                    )
                    return response_data

                # Any non-200 response - retry with next config
                logger.warning(f"Google API error {response.status_code} with config #{config.get_current_index() + 1}, trying next config")

                # Log error response for debugging
                try:
                    error_json = json.loads(response.content.decode('utf-8', errors='replace'))
                    logger.error(f"Error response: {json.dumps(error_json, indent=2)}")
                except:
                    logger.error(f"Error response (raw): {response.content[:500]}")

                # Raise exception to trigger retry with next config
                raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            logger.warning(f"Error with config #{config.get_current_index() + 1}: {e}")

            # Increment retry counter
            retry_count += 1

            # Check if we've tried all configs
            if retry_count >= max_retries:
                # We've tried all configs
                logger.error(f"All {max_retries} Gemini config(s) failed")

                # Return a 400 error to prevent client auto-retry
                error_response = _create_error_response(
                    400,
                    "Bad Request",
                    f"All configured Gemini API endpoints are currently unavailable. Tried {max_retries} config(s)."
                )
                return error_response

            # Move to next config
            config.current_index = (config.current_index + 1) % max_retries
            logger.info(f"Failover to Gemini config #{config.get_current_index() + 1}")
            # Continue loop with new config

    # Should not reach here, but just in case
    logger.error("Unexpected: exited retry loop without returning")
    error_response = _create_error_response(
        400,
        "Bad Request",
        "All configured Gemini API endpoints are currently unavailable."
    )
    return error_response


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
        # Skip certain headers that are not valid or already handled
        if key.lower() in ['transfer-encoding', 'connection', 'content-encoding']:
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
