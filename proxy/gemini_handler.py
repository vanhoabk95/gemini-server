"""
Gemini API handler module.

This module handles requests to the Gemini API proxy.
"""

import re
import json
import asyncio
from urllib.parse import urlencode

from proxy.logger import get_logger
from proxy.gemini_config import get_gemini_config
from proxy.gemini_usage_tracker import track_request

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


async def handle_gemini_request(writer, request_data, client_address):
    """
    Handle a Gemini API request.

    Args:
        writer (asyncio.StreamWriter): The client stream writer
        request_data (bytes): The raw request data
        client_address (tuple): The client's address

    Returns:
        bool: True if successful, False otherwise
    """
    config = get_gemini_config()

    if not config.is_enabled():
        logger.warning(f"LLM proxy request from {client_address[0]} but feature is disabled")
        error_response = _create_error_response(
            400,
            "Bad Request",
            "LLM Server is not enabled"
        )
        writer.write(error_response)
        await writer.drain()
        return False

    try:
        # Parse the request
        method, path, headers, body = _parse_gemini_request(request_data)

        if not path:
            logger.error(f"Could not parse LLM request from {client_address[0]}")
            error_response = _create_error_response(400, "Bad Request", "Invalid request format")
            writer.write(error_response)
            await writer.drain()
            return False

        logger.info(f"LLM API request from {client_address[0]}: {method} {path}")

        # Replace model in path with configured model
        path = _replace_model_in_path(path, config.get_model())

        # Forward to LLM API
        response_data = await _forward_to_google(method, path, headers, body, config)

        if response_data:
            # Send response back to client
            writer.write(response_data)
            await writer.drain()
            return True
        else:
            error_response = _create_error_response(502, "Bad Gateway", "Failed to reach LLM server")
            writer.write(error_response)
            await writer.drain()
            return False

    except Exception as e:
        logger.error(f"Error handling LLM request: {e}")
        error_response = _create_error_response(500, "Internal Server Error", "Internal server error")
        writer.write(error_response)
        await writer.drain()
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
        logger.error(f"Error parsing LLM request: {e}")
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


async def _forward_to_google(method, path, headers, body, config):
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
            logger.info(f"Using config #{config.get_current_index() + 1}/{max_retries}: model={model}")

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

            # Make asynchronous request with httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                if method == 'POST':
                    response = await client.post(url, content=body, headers=request_headers)
                elif method == 'GET':
                    response = await client.get(url, headers=request_headers)
                else:
                    logger.warning(f"Unsupported method: {method}")
                    return None

                # Check if request was successful
                if response.status_code == 200:
                    # Success - update status to healthy
                    config.update_status(status='healthy', error_message=None)

                    # Track successful request
                    track_request(config.get_current_index(), success=True)

                    logger.info(f"Response: {response.status_code} - {len(response.content)} bytes")
                    response_data = _build_http_response(
                        response.status_code,
                        response.reason_phrase,
                        response.headers,
                        response.content
                    )
                    return response_data

                # Any non-200 response - retry with next config
                logger.warning(f"Config #{config.get_current_index() + 1} failed with status {response.status_code}")

                # Update status based on error code
                if response.status_code == 429:
                    config.update_status(status='rate_limited', error_message=f"Rate limited: {response.status_code}")
                elif response.status_code >= 500:
                    config.update_status(status='server_error', error_message=f"Server error: {response.status_code}")
                else:
                    config.update_status(status='failed', error_message=f"API error: {response.status_code}")

                # Track failed request
                track_request(config.get_current_index(), success=False)

                # Raise exception to trigger retry with next config
                raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            logger.warning(f"Error with config #{config.get_current_index() + 1}: {e}")

            # Update status based on exception type
            error_str = str(e).lower()
            if 'timeout' in error_str:
                config.update_status(status='timeout', error_message=str(e))
            elif 'connection' in error_str:
                config.update_status(status='connection_error', error_message=str(e))
            else:
                config.update_status(status='failed', error_message=str(e))

            # Track failed request (only if not already tracked)
            # Check if exception is from our own raise above (already tracked)
            if 'API error:' not in str(e):
                track_request(config.get_current_index(), success=False)

            # Increment retry counter
            retry_count += 1

            # Check if we've tried all configs
            if retry_count >= max_retries:
                # We've tried all configs
                logger.error(f"All {max_retries} config(s) failed")

                # Return a 400 error to prevent client auto-retry
                error_response = _create_error_response(
                    400,
                    "Bad Request",
                    "LLM server is currently unavailable"
                )
                return error_response

            # Move to next config
            config.current_index = (config.current_index + 1) % max_retries
            logger.info(f"Failover to config #{config.get_current_index() + 1}")
            # Continue loop with new config

    # Should not reach here, but just in case
    logger.error("Unexpected: exited retry loop without returning")
    error_response = _create_error_response(
        400,
        "Bad Request",
        "LLM server is currently unavailable"
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
