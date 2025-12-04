"""
Gemini configuration module.

This module manages configuration for the Gemini API proxy feature.
Supports multiple configurations with automatic failover.
"""

import os
import json
from pathlib import Path
from datetime import datetime


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
        self.config_file_path = None  # Store config file path for saving
        self.last_file_mtime = None  # Track last modification time for auto-reload

        # Load from config file if provided
        if config_file and Path(config_file).exists():
            self.config_file_path = config_file
            self._load_from_file(config_file)
            # Track file modification time
            try:
                self.last_file_mtime = Path(config_file).stat().st_mtime
            except:
                pass

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
                'api_key': env_api_key,
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
            if cfg.get('api_key'):
                # Set defaults for missing fields
                if 'model' not in cfg:
                    cfg['model'] = self.DEFAULT_MODEL
                if 'api_base' not in cfg:
                    cfg['api_base'] = self.DEFAULT_API_BASE
                # Initialize status fields if not present
                if 'status' not in cfg:
                    cfg['status'] = 'unknown'
                if 'last_check' not in cfg:
                    cfg['last_check'] = None
                if 'error_message' not in cfg:
                    cfg['error_message'] = None
                # Initialize daily_limit if not present
                if 'daily_limit' not in cfg:
                    cfg['daily_limit'] = 1000
                # Ensure daily_limit is valid
                if not isinstance(cfg['daily_limit'], (int, float)) or cfg['daily_limit'] < 0:
                    cfg['daily_limit'] = 1000
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
        return cfg.get('api_key') if cfg else None

    def get_model(self):
        """Get Gemini model name from current config."""
        cfg = self.get_current_config()
        return cfg.get('model', self.DEFAULT_MODEL) if cfg else self.DEFAULT_MODEL

    def get_api_base(self):
        """Get Google API base URL from current config."""
        cfg = self.get_current_config()
        return cfg.get('api_base', self.DEFAULT_API_BASE) if cfg else self.DEFAULT_API_BASE

    def get_daily_limit(self, index=None):
        """
        Get daily request limit from a config.

        Args:
            index (int, optional): Config index. If None, uses current_index

        Returns:
            int: Daily limit (default: 1000)
        """
        if index is None:
            cfg = self.get_current_config()
        else:
            if 0 <= index < len(self.configs):
                cfg = self.configs[index]
            else:
                cfg = None

        return cfg.get('daily_limit', 1000) if cfg else 1000

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

    def update_status(self, index=None, status='unknown', error_message=None, auto_save=True):
        """
        Update the status of a configuration.

        Args:
            index (int, optional): Config index to update. If None, uses current_index
            status (str): Status value (e.g., 'healthy', 'failed', 'timeout', 'rate_limited')
            error_message (str, optional): Error message if status is failed
            auto_save (bool): Automatically save to file after update (default: True)
        """
        if index is None:
            index = self.current_index

        if 0 <= index < len(self.configs):
            self.configs[index]['status'] = status
            self.configs[index]['last_check'] = datetime.now().isoformat()
            self.configs[index]['error_message'] = error_message

            # Auto-save to file if enabled
            if auto_save and self.config_file_path:
                self.save_to_file()

    def save_to_file(self, file_path=None):
        """
        Save current configuration (including status) back to JSON file.
        
        This method intelligently merges status updates with the current file content
        to avoid overwriting manually edited fields like api_key, model, or daily_limit.

        Args:
            file_path (str, optional): Path to save to. If None, uses original config_file_path
        """
        save_path = file_path or self.config_file_path

        if not save_path:
            # Use logging if available, otherwise print
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.debug("No config file path specified, cannot save status")
            except:
                print("WARNING: No config file path specified, cannot save status")
            return False

        try:
            # Read current file content to preserve manual edits
            file_configs = []
            if Path(save_path).exists():
                try:
                    with open(save_path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    # Parse file data (same logic as _load_from_file)
                    if isinstance(file_data, list):
                        file_configs = file_data
                    elif isinstance(file_data, dict) and 'configs' in file_data:
                        file_configs = file_data['configs']
                    elif isinstance(file_data, dict):
                        file_configs = [file_data]
                except Exception as read_error:
                    # If we can't read the file, fall back to saving our in-memory config
                    try:
                        from proxy.logger import get_logger
                        logger = get_logger()
                        logger.warning(f"Could not read config file for merge: {read_error}, using in-memory config")
                    except:
                        print(f"WARNING: Could not read config file for merge: {read_error}")
                    file_configs = []

            # Merge: preserve file config fields, only update status fields from memory
            merged_configs = []
            for idx, mem_cfg in enumerate(self.configs):
                if idx < len(file_configs):
                    # Start with file config to preserve manual edits
                    merged = file_configs[idx].copy()
                    
                    # Only update status-related fields from memory
                    merged['status'] = mem_cfg.get('status', 'unknown')
                    merged['last_check'] = mem_cfg.get('last_check')
                    merged['error_message'] = mem_cfg.get('error_message')
                    
                    merged_configs.append(merged)
                else:
                    # New config added in memory that doesn't exist in file
                    merged_configs.append(mem_cfg)
            
            # If file has more configs than memory, preserve them
            if len(file_configs) > len(self.configs):
                for idx in range(len(self.configs), len(file_configs)):
                    merged_configs.append(file_configs[idx])

            # Save merged data
            output_data = {
                "configs": merged_configs
            }

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            # Log success if logger available
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.debug(f"Config status saved to {save_path}")
            except:
                pass

            return True
        except Exception as e:
            # Use logging if available, otherwise print
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.error(f"Error saving config to file: {e}")
            except:
                print(f"Error saving config to file: {e}")
            return False

    def get_status(self, index=None):
        """
        Get the status of a configuration.

        Args:
            index (int, optional): Config index. If None, uses current_index

        Returns:
            dict: Status info with keys: status, last_check, error_message
        """
        if index is None:
            index = self.current_index

        if 0 <= index < len(self.configs):
            cfg = self.configs[index]
            return {
                'status': cfg.get('status', 'unknown'),
                'last_check': cfg.get('last_check'),
                'error_message': cfg.get('error_message')
            }
        return None

    def reload_from_file(self):
        """
        Reload configuration from file, preserving status information.
        This allows hot-reloading of API keys and other settings without server restart.
        
        Returns:
            bool: True if config was reloaded, False otherwise
        """
        if not self.config_file_path or not Path(self.config_file_path).exists():
            return False
        
        try:
            # Save current status information
            status_backup = []
            for cfg in self.configs:
                status_backup.append({
                    'status': cfg.get('status', 'unknown'),
                    'last_check': cfg.get('last_check'),
                    'error_message': cfg.get('error_message')
                })
            
            # Reload from file
            self._load_from_file(self.config_file_path)
            self._validate()
            
            # Restore status information for configs that still exist
            for idx in range(min(len(self.configs), len(status_backup))):
                self.configs[idx]['status'] = status_backup[idx]['status']
                self.configs[idx]['last_check'] = status_backup[idx]['last_check']
                self.configs[idx]['error_message'] = status_backup[idx]['error_message']
            
            # Update last modification time
            try:
                self.last_file_mtime = Path(self.config_file_path).stat().st_mtime
            except:
                pass
            
            # Log reload
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.info(f"Config reloaded from {self.config_file_path}")
            except:
                print(f"Config reloaded from {self.config_file_path}")
            
            return True
        except Exception as e:
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.error(f"Error reloading config: {e}")
            except:
                print(f"Error reloading config: {e}")
            return False
    
    def check_and_reload(self):
        """
        Check if config file has been modified and reload if needed.
        
        Returns:
            bool: True if config was reloaded, False otherwise
        """
        if not self.config_file_path or not Path(self.config_file_path).exists():
            return False
        
        try:
            current_mtime = Path(self.config_file_path).stat().st_mtime
            if self.last_file_mtime is None or current_mtime > self.last_file_mtime:
                return self.reload_from_file()
        except Exception as e:
            pass
        
        return False

    def __str__(self):
        """String representation of config."""
        if not self.is_enabled():
            return "Gemini Proxy Config: Disabled"

        cfg = self.get_current_config()
        api_key = cfg.get('api_key', '')
        masked_key = '***' + api_key[-4:] if api_key and len(api_key) > 4 else 'Not set'

        status_info = self.get_status()
        status_str = f"  Status: {status_info['status']}"
        if status_info['last_check']:
            status_str += f" (checked: {status_info['last_check']})"
        if status_info['error_message']:
            status_str += f"\n  Error: {status_info['error_message']}"

        return (
            f"Gemini Proxy Config:\n"
            f"  Enabled: {self.enabled}\n"
            f"  Total Configs: {len(self.configs)}\n"
            f"  Current Config: #{self.current_index + 1}\n"
            f"  Model: {cfg.get('model', self.DEFAULT_MODEL)}\n"
            f"  API Base: {cfg.get('api_base', self.DEFAULT_API_BASE)}\n"
            f"  API Key: {masked_key}\n"
            f"{status_str}"
        )


# Global instance
_gemini_config = None


def get_gemini_config(config_file=None, auto_reload=True):
    """
    Get or create the global Gemini configuration instance.
    Automatically reloads config if file has been modified.

    Args:
        config_file (str, optional): Path to config file
        auto_reload (bool): Whether to automatically reload if file changed (default: True)

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
    elif auto_reload:
        # Check if config file has been modified and reload if needed
        _gemini_config.check_and_reload()

    return _gemini_config
