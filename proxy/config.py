"""
Configuration module for the proxy server.

This module handles loading and parsing configuration options from command-line
arguments or configuration files.
"""

import argparse
import os


class Config:
    """
    Configuration class for the proxy server.
    
    Handles parsing and storing configuration options for the proxy server.
    """
    
    def __init__(self):
        """Initialize default configuration values."""
        self.host = '0.0.0.0'
        self.port = 8888
        self.max_connections = 20
        self.log_level = 'WARNING'
    
    def load_from_args(self, args=None):
        """
        Load configuration from command-line arguments.
        
        Args:
            args (list, optional): Command-line arguments. Defaults to None.
        """
        parser = argparse.ArgumentParser(description='Simple Python Proxy Server')
        
        parser.add_argument('--host', default=self.host,
                          help=f'IP address to bind (default: {self.host})')
        
        parser.add_argument('--port', type=int, default=self.port,
                          help=f'Port to listen on (default: {self.port})')
        
        parser.add_argument('--max-connections', type=int, default=self.max_connections,
                          help=f'Maximum number of connections (default: {self.max_connections})')
        
        parser.add_argument('--log-level', default=self.log_level, 
                          choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                          help=f'Log level (default: {self.log_level})')
        
        parsed_args = parser.parse_args(args)
        
        # Update configuration with parsed arguments
        self.host = parsed_args.host
        self.port = parsed_args.port
        self.max_connections = parsed_args.max_connections
        self.log_level = parsed_args.log_level
    
    def __str__(self):
        """Return a string representation of the configuration."""
        return (f"Configuration:\n"
                f"  Host: {self.host}\n"
                f"  Port: {self.port}\n"
                f"  Max Connections: {self.max_connections}\n"
                f"  Log Level: {self.log_level}")


def get_config(args=None):
    """
    Create and load a configuration instance.
    
    Args:
        args (list, optional): Command-line arguments. Defaults to None.
        
    Returns:
        Config: The loaded configuration instance
    """
    config = Config()
    config.load_from_args(args)
    return config 