# Simple Python Proxy Server

A lightweight HTTP/HTTPS proxy server implemented in Python using only standard libraries.

## Overview

This proxy server accepts HTTP and HTTPS requests on a specified port and forwards them to the appropriate destination. It's designed to run on a PC and allow other machines within the LAN network to route web traffic through it.

## Features

- Configurable listening IP address and port
- Support for both HTTP and HTTPS (via CONNECT method)
- Multithreaded request handling for concurrent connections
- Detailed logging of all transactions
- Command-line configuration options
- Lightweight and easy to modify

## Usage

Start the proxy server with default settings:

```bash
python main.py
```

Configure the proxy server with command line arguments:

```bash
python main.py --host 0.0.0.0 --port 8888 --max-connections 50 --log-level INFO
```

### Client Configuration

To use this proxy server in your LAN, configure your client devices as follows:

#### For Browsers (Chrome, Firefox, etc.)
1. Go to browser settings
2. Find proxy settings (usually under Network or Advanced settings)
3. Enter your proxy server's IP address and port

#### For System-wide Settings (Windows)
1. Open Settings > Network & Internet > Proxy
2. Enable "Manual proxy setup"
3. Enter your proxy server's IP address and port

#### For System-wide Settings (macOS)
1. Open System Preferences > Network > Advanced > Proxies
2. Check "Web Proxy (HTTP)" and "Secure Web Proxy (HTTPS)"
3. Enter your proxy server's IP address and port for both

## How It Works

### HTTP Proxying
For HTTP requests, the proxy forwards the request to the target server and relays the response back to the client.

### HTTPS Proxying
For HTTPS requests:
1. Client sends a CONNECT request to establish a tunnel
2. Proxy creates a connection to the target server
3. Proxy returns a "200 Connection Established" response to the client
4. Client and target server perform SSL/TLS handshake through the proxy tunnel
5. Proxy forwards encrypted data in both directions without interpreting it

## Configuration

The proxy server can be configured using command-line arguments:

- `--host`: IP address to bind to (default: 0.0.0.0)
- `--port`: Port to listen on (default: 8888)
- `--max-connections`: Maximum number of concurrent connections (default: 20)
- `--log-level`: Logging level (default: INFO)

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard libraries)

## Project Structure

- `proxy/`: Core proxy server implementation
  - `server.py`: Server module for listening and accepting connections
  - `handler.py`: Client handler module for processing requests
  - `forwarder.py`: Forwarding module for communicating with target servers
  - `config.py`: Configuration module for handling settings
  - `logger.py`: Logging module for monitoring and troubleshooting
- `tests/`: Unit tests for the proxy server components
- `main.py`: Entry point for the application 