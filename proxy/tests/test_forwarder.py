"""
Unit tests for the forwarder module.
"""

import unittest
from unittest.mock import MagicMock, patch

from proxy.forwarder import parse_request


class TestForwarder(unittest.TestCase):
    """Tests for the forwarder module."""
    
    def test_parse_request_absolute_url(self):
        """Test parsing a request with an absolute URL."""
        request_data = (
            b"GET http://example.com/path?query=value HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"User-Agent: Mozilla/5.0\r\n"
            b"\r\n"
        )
        
        method, url, host, port, path, headers = parse_request(request_data)
        
        self.assertEqual(method, "GET")
        self.assertEqual(url, "http://example.com/path?query=value")
        self.assertEqual(host, "example.com")
        self.assertEqual(port, 80)
        self.assertEqual(path, "/path?query=value")
        self.assertIn("user-agent", headers)
        self.assertEqual(headers["user-agent"], "Mozilla/5.0")
    
    def test_parse_request_relative_url(self):
        """Test parsing a request with a relative URL."""
        request_data = (
            b"GET /path?query=value HTTP/1.1\r\n"
            b"Host: example.com:8080\r\n"
            b"User-Agent: Mozilla/5.0\r\n"
            b"\r\n"
        )
        
        method, url, host, port, path, headers = parse_request(request_data)
        
        self.assertEqual(method, "GET")
        self.assertEqual(url, "/path?query=value")
        self.assertEqual(host, "example.com")
        self.assertEqual(port, 8080)
        self.assertEqual(path, "/path?query=value")
        self.assertIn("user-agent", headers)
        self.assertEqual(headers["user-agent"], "Mozilla/5.0")
    
    def test_parse_request_invalid(self):
        """Test parsing an invalid request."""
        request_data = b"INVALID REQUEST\r\n\r\n"
        
        method, url, host, port, path, headers = parse_request(request_data)
        
        self.assertIsNone(method)
        self.assertIsNone(url)
        self.assertIsNone(host)
        self.assertIsNone(port)
        self.assertIsNone(path)
        self.assertIsNone(headers)


if __name__ == "__main__":
    unittest.main() 