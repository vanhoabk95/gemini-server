"""
Gemini configuration module.

This module manages configuration for the Gemini API proxy feature.
Supports multiple configurations with automatic failover.
"""

import os
import json
from pathlib import Path


class GeminiConfig:
    """Configuration for Gemini API proxy with failover support."""

    # Default values
    DEFAULT_MODEL = "gemini-1.5-flash"
    DEFAULT_API_BASE = "https://generativelanguage.googleapis.com"

    def __init__(self, config_file=None):
        """
        Initialize Gemini configuration.

        Args:
            config_file (str, optional): Path to JSON config file
        """
        self.configs = []  # List of config dicts
        self.current_index = 0  # Current active config index
        self.enabled = False

        # Load from config file if provided
        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)

        # Override with environment variables if set
        self._load_from_env()

        # Validate configuration
        self._validate()

    def _load_from_file(self, config_file):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Support multiple formats
            if isinstance(data, list):
                # Direct array format
                self.configs = data
            elif isinstance(data, dict):
                if 'configs' in data:
                    # Object with configs key
                    self.configs = data['configs']
                    # Set enabled from global setting if present
                    if data.get('enabled') is not None:
                        self.enabled = data['enabled']
                else:
                    # Single config object - convert to list
                    self.configs = [data]

            # Set enabled flag from first config if not already set
            if not self.enabled and self.configs and self.configs[0].get('enabled') is not None:
                self.enabled = self.configs[0]['enabled']

        except Exception as e:
            print(f"Error loading Gemini config from file: {e}")

    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_api_key = os.getenv('GOOGLE_API_KEY')
        env_model = os.getenv('GEMINI_MODEL')
        env_api_base = os.getenv('GEMINI_API_BASE')
        env_enabled = os.getenv('GEMINI_ENABLED')

        # If env vars are set, add as a config
        if env_api_key:
            env_config = {
                'google_api_key': env_api_key,
                'model': env_model or self.DEFAULT_MODEL,
                'api_base': env_api_base or self.DEFAULT_API_BASE,
                'enabled': True
            }
            # Prepend env config (highest priority)
            self.configs.insert(0, env_config)

        if env_enabled is not None:
            self.enabled = env_enabled.lower() in ('true', '1', 'yes')

    def _validate(self):
        """Validate configuration."""
        # Filter out invalid configs (no API key)
        valid_configs = []
        for cfg in self.configs:
            if cfg.get('google_api_key'):
                # Set defaults for missing fields
                if 'model' not in cfg:
                    cfg['model'] = self.DEFAULT_MODEL
                if 'api_base' not in cfg:
                    cfg['api_base'] = self.DEFAULT_API_BASE
                valid_configs.append(cfg)

        self.configs = valid_configs

        # If enabled but no valid configs, disable
        if self.enabled and not self.configs:
            print("WARNING: Gemini proxy is enabled but no valid API keys provided. Feature disabled.")
            self.enabled = False

        # If we have valid configs, enable automatically
        if self.configs and not self.enabled:
            self.enabled = True

    def is_enabled(self):
        """Check if Gemini proxy is enabled."""
        return self.enabled and len(self.configs) > 0

    def get_current_config(self):
        """
        Get the current active configuration.

        Returns:
            dict: Current config or None
        """
        if not self.configs:
            return None
        return self.configs[self.current_index]

    def get_api_key(self):
        """Get Google API key from current config."""
        cfg = self.get_current_config()
        return cfg['google_api_key'] if cfg else None

    def get_model(self):
        """Get Gemini model name from current config."""
        cfg = self.get_current_config()
        return cfg.get('model', self.DEFAULT_MODEL) if cfg else self.DEFAULT_MODEL

    def get_api_base(self):
        """Get Google API base URL from current config."""
        cfg = self.get_current_config()
        return cfg.get('api_base', self.DEFAULT_API_BASE) if cfg else self.DEFAULT_API_BASE

    def rotate_to_next(self):
        """
        Rotate to the next configuration in the list.
        Wraps around to the beginning when reaching the end.

        Returns:
            bool: True if rotated, False if no other configs available
        """
        if len(self.configs) <= 1:
            return False

        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.configs)

        print(f"Rotating Gemini config from #{old_index + 1} to #{self.current_index + 1}")
        return True

    def try_next_config(self, start_index):
        """
        Try to move to the next config for failover.

        Args:
            start_index (int): The index where we started trying

        Returns:
            bool: True if there's another config to try, False if we've tried all
        """
        if len(self.configs) <= 1:
            return False

        # Move to next config
        self.current_index = (self.current_index + 1) % len(self.configs)

        # Check if we've completed a full circle
        if self.current_index == start_index:
            return False

        return True

    def get_config_count(self):
        """Get total number of available configurations."""
        return len(self.configs)

    def get_current_index(self):
        """Get current configuration index (0-based)."""
        return self.current_index

    def __str__(self):
        """String representation of config."""
        if not self.is_enabled():
            return "Gemini Proxy Config: Disabled"

        cfg = self.get_current_config()
        api_key = cfg.get('google_api_key', '')
        masked_key = '***' + api_key[-4:] if api_key and len(api_key) > 4 else 'Not set'

        return (
            f"Gemini Proxy Config:\n"
            f"  Enabled: {self.enabled}\n"
            f"  Total Configs: {len(self.configs)}\n"
            f"  Current Config: #{self.current_index + 1}\n"
            f"  Model: {cfg.get('model', self.DEFAULT_MODEL)}\n"
            f"  API Base: {cfg.get('api_base', self.DEFAULT_API_BASE)}\n"
            f"  API Key: {masked_key}"
        )


# Global instance
_gemini_config = None


def get_gemini_config(config_file=None):
    """
    Get or create the global Gemini configuration instance.

    Args:
        config_file (str, optional): Path to config file

    Returns:
        GeminiConfig: The global configuration instance
    """
    global _gemini_config

    if _gemini_config is None:
        # Try default config file locations
        default_paths = [
            'gemini_config.json',
            'config/gemini_config.json',
            '.gemini_config.json'
        ]

        config_path = config_file
        if not config_path:
            for path in default_paths:
                if Path(path).exists():
                    config_path = path
                    break

        _gemini_config = GeminiConfig(config_path)

    return _gemini_config
