"""
Request statistics tracking module.

This module tracks and stores statistics about incoming requests per IP address.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class RequestStats:
    """
    Thread-safe request statistics tracker.

    Tracks requests per IP address including:
    - Total requests count
    - Request types (Gemini only)
    - Success/failure counts
    - First and last seen timestamps
    """

    def __init__(self, stats_dir='stats', auto_save_interval=60):
        """
        Initialize request statistics tracker.

        Args:
            stats_dir (str): Directory to store stats files
            auto_save_interval (int): Auto-save interval in seconds (0 to disable)
        """
        self.stats_dir = stats_dir
        self.auto_save_interval = auto_save_interval
        self.stats_file = None

        # In-memory stats storage
        self.stats = defaultdict(lambda: {
            'total_requests': 0,
            'gemini_requests': 0,
            'first_seen': None,
            'last_seen': None,
            'success_count': 0,
            'failed_count': 0
        })

        # Thread safety
        self._lock = asyncio.Lock()
        self._auto_save_task = None
        self._enabled = False

    async def start(self):
        """Start the stats tracker and auto-save task."""
        # Create stats directory
        os.makedirs(self.stats_dir, exist_ok=True)

        # Set current stats file path
        self.stats_file = os.path.join(self.stats_dir, 'request_stats.json')

        # Load existing stats
        await self._load_from_file()

        # Start auto-save task
        if self.auto_save_interval > 0:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())

        self._enabled = True

    async def stop(self):
        """Stop the stats tracker and save final state."""
        self._enabled = False

        # Cancel auto-save task
        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass

        # Final save
        await self.save_to_file()

    async def track_request(self, ip_address, request_type='gemini', success=True):
        """
        Track a single request.

        Args:
            ip_address (str): Client IP address
            request_type (str): Type of request ('gemini' only)
            success (bool): Whether the request was successful
        """
        if not self._enabled:
            return

        async with self._lock:
            now = datetime.now().isoformat()

            # Update stats
            ip_stats = self.stats[ip_address]
            ip_stats['total_requests'] += 1

            # Track request type (all requests are Gemini now)
            ip_stats['gemini_requests'] += 1

            # Track success/failure
            if success:
                ip_stats['success_count'] += 1
            else:
                ip_stats['failed_count'] += 1

            # Update timestamps
            if ip_stats['first_seen'] is None:
                ip_stats['first_seen'] = now
            ip_stats['last_seen'] = now

    async def get_stats(self, ip_address=None):
        """
        Get statistics.

        Args:
            ip_address (str, optional): Get stats for specific IP. If None, returns all stats.

        Returns:
            dict: Statistics data
        """
        async with self._lock:
            if ip_address:
                return dict(self.stats.get(ip_address, {}))
            else:
                return {ip: dict(stats) for ip, stats in self.stats.items()}

    async def get_top_ips(self, limit=10):
        """
        Get top IP addresses by request count.

        Args:
            limit (int): Maximum number of IPs to return

        Returns:
            list: List of (ip, stats) tuples sorted by total_requests
        """
        async with self._lock:
            sorted_ips = sorted(
                self.stats.items(),
                key=lambda x: x[1]['total_requests'],
                reverse=True
            )
            return [(ip, dict(stats)) for ip, stats in sorted_ips[:limit]]

    async def save_to_file(self, file_path=None):
        """
        Save statistics to JSON file.

        Args:
            file_path (str, optional): Path to save to. If None, uses default stats file.

        Returns:
            bool: True if successful, False otherwise
        """
        save_path = file_path or self.stats_file

        if not save_path:
            return False

        try:
            async with self._lock:
                # Convert defaultdict to regular dict for JSON serialization
                stats_dict = {ip: dict(stats) for ip, stats in self.stats.items()}

                # Add metadata
                output = {
                    'generated_at': datetime.now().isoformat(),
                    'total_ips': len(stats_dict),
                    'total_requests': sum(s['total_requests'] for s in stats_dict.values()),
                    'stats': stats_dict
                }

                # Write to file
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            # Log error if logger available
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.error(f"Error saving request stats: {e}")
            except:
                print(f"Error saving request stats: {e}")
            return False

    async def _load_from_file(self):
        """Load statistics from file if it exists."""
        if not self.stats_file or not Path(self.stats_file).exists():
            return

        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load stats (handle both old and new format)
            stats_data = data.get('stats', data)

            async with self._lock:
                for ip, ip_stats in stats_data.items():
                    # Skip metadata keys
                    if ip in ['generated_at', 'total_ips', 'total_requests']:
                        continue
                    self.stats[ip] = ip_stats

            # Log success if logger available
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.info(f"Loaded request stats: {len(self.stats)} IPs tracked")
            except:
                pass

        except Exception as e:
            # Log error if logger available
            try:
                from proxy.logger import get_logger
                logger = get_logger()
                logger.warning(f"Could not load existing stats file: {e}")
            except:
                print(f"Could not load existing stats file: {e}")

    async def _auto_save_loop(self):
        """Background task to auto-save stats periodically."""
        while self._enabled:
            try:
                await asyncio.sleep(self.auto_save_interval)
                await self.save_to_file()

                # Log if logger available
                try:
                    from proxy.logger import get_logger
                    logger = get_logger()
                    logger.debug("Auto-saved request stats")
                except:
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error if logger available
                try:
                    from proxy.logger import get_logger
                    logger = get_logger()
                    logger.error(f"Error in auto-save loop: {e}")
                except:
                    print(f"Error in auto-save loop: {e}")


# Global instance
_request_stats = None


async def get_request_stats(stats_dir='stats', auto_save_interval=60):
    """
    Get or create the global request stats instance.

    Args:
        stats_dir (str): Directory to store stats files
        auto_save_interval (int): Auto-save interval in seconds

    Returns:
        RequestStats: The global stats instance
    """
    global _request_stats

    if _request_stats is None:
        _request_stats = RequestStats(stats_dir, auto_save_interval)
        await _request_stats.start()

    return _request_stats


def get_request_stats_sync():
    """
    Get the global request stats instance (sync version).

    Returns:
        RequestStats: The global stats instance or None if not initialized
    """
    return _request_stats
