"""
Unit tests for HTTPS functionality.
"""

import unittest
from unittest.mock import MagicMock, patch, call

from proxy.forwarder import parse_request, create_https_tunnel


class TestHttps(unittest.TestCase):
    """Tests for HTTPS functionality."""
    
    def test_parse_connect_request(self):
        """Test parsing a CONNECT request."""
        request_data = (
            b"CONNECT example.com:443 HTTP/1.1\r\n"
            b"Host: example.com:443\r\n"
            b"User-Agent: Mozilla/5.0\r\n"
            b"\r\n"
        )
        
        method, url, host, port, path, headers = parse_request(request_data)
        
        self.assertEqual(method, "CONNECT")
        self.assertEqual(url, "example.com:443")
        self.assertEqual(host, "example.com")
        self.assertEqual(port, 443)
        self.assertEqual(path, "")
        self.assertEqual(headers, {})
    
    def test_parse_connect_request_default_port(self):
        """Test parsing a CONNECT request with default port."""
        request_data = (
            b"CONNECT example.com HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"User-Agent: Mozilla/5.0\r\n"
            b"\r\n"
        )
        
        method, url, host, port, path, headers = parse_request(request_data)
        
        self.assertEqual(method, "CONNECT")
        self.assertEqual(url, "example.com")
        self.assertEqual(host, "example.com")
        self.assertEqual(port, 443)  # Default HTTPS port
        self.assertEqual(path, "")
        self.assertEqual(headers, {})
    
    @patch('select.select')
    @patch('socket.socket')
    def test_create_https_tunnel_simplified(self, mock_socket, mock_select):
        """Test creating an HTTPS tunnel with simplified mocking."""
        # Set up the mocks
        mock_client_socket = MagicMock()
        mock_server_socket = MagicMock()
        mock_socket.return_value = mock_server_socket
        
        # Set up some client data and server data for the tunnel
        client_data = b"Client data"
        server_data = b"Server data"
        
        # Configure the client and server socket mocks
        mock_client_socket.recv.return_value = client_data
        mock_server_socket.recv.return_value = server_data
        
        # Make the select mock exit immediately after one iteration
        mock_select.side_effect = [
            ([], [], [mock_client_socket])  # Error on client socket to exit loop
        ]
        
        # Call the function under test
        result = create_https_tunnel(
            mock_client_socket,
            "example.com",
            443,
            ("192.168.1.100", 12345)
        )
        
        # Verify the basic operations
        mock_server_socket.connect.assert_called_with(("example.com", 443))
        mock_client_socket.sendall.assert_called_with(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        mock_server_socket.close.assert_called_once()
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main() 