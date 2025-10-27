"""
Gemini Usage Tracker Module

Tracks daily usage of Gemini API requests per configuration with history.
Automatically resets counts at midnight (local time).
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


# Configuration
HISTORY_FILE = 'stats/gemini_usage_history.json'


def get_today_date():
    """
    Get current date string in YYYY-MM-DD format (local time).

    Returns:
        str: Date string (e.g., "2025-01-17")
    """
    return datetime.now().strftime('%Y-%m-%d')


def load_history():
    """
    Load usage history from JSON file.

    Returns:
        dict: History data structure
            {
                "config_0": {
                    "2025-01-15": {"success": 123, "failed": 5, "total": 128},
                    "2025-01-16": {"success": 456, "failed": 2, "total": 458}
                },
                "config_1": {...}
            }
    """
    history_path = Path(HISTORY_FILE)

    if not history_path.exists():
        return {}

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading usage history: {e}")
        return {}


def save_history(history_data):
    """
    Save usage history to JSON file.

    Args:
        history_data (dict): History data to save

    Returns:
        bool: True if successful, False otherwise
    """
    history_path = Path(HISTORY_FILE)

    # Create stats directory if it doesn't exist
    history_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving usage history: {e}")
        return False


def track_request(config_index, success=True):
    """
    Track a single request for a specific config.

    Automatically handles date changes and maintains history.

    Args:
        config_index (int): Index of the config (0-based)
        success (bool): True if request was successful, False if failed

    Returns:
        bool: True if tracking was successful
    """
    try:
        history = load_history()
        today = get_today_date()

        config_key = f"config_{config_index}"

        # Initialize config entry if not exists
        if config_key not in history:
            history[config_key] = {}

        # Initialize today's entry if not exists (auto-reset)
        if today not in history[config_key]:
            history[config_key][today] = {
                "success": 0,
                "failed": 0,
                "total": 0
            }

        # Increment counters
        if success:
            history[config_key][today]["success"] += 1
        else:
            history[config_key][today]["failed"] += 1

        history[config_key][today]["total"] += 1

        # Save to file
        return save_history(history)

    except Exception as e:
        print(f"Error tracking request: {e}")
        return False


def get_today_usage(config_index):
    """
    Get today's usage for a specific config.

    Args:
        config_index (int): Index of the config (0-based)

    Returns:
        dict: Today's usage stats
            {"success": 123, "failed": 5, "total": 128}
            Returns zeros if no data for today
    """
    history = load_history()
    today = get_today_date()
    config_key = f"config_{config_index}"

    if config_key in history and today in history[config_key]:
        return history[config_key][today]

    return {"success": 0, "failed": 0, "total": 0}


def get_usage_range(config_index, days=30):
    """
    Get usage data for the last N days for a specific config.

    Args:
        config_index (int): Index of the config (0-based)
        days (int): Number of days to retrieve (default: 30)

    Returns:
        dict: Usage data for each date
            {
                "2025-01-15": {"success": 123, "failed": 5, "total": 128},
                "2025-01-16": {"success": 456, "failed": 2, "total": 458},
                ...
            }
            Sorted by date (oldest to newest)
    """
    history = load_history()
    config_key = f"config_{config_index}"

    if config_key not in history:
        return {}

    # Calculate date range
    today = datetime.now()
    start_date = today - timedelta(days=days-1)

    # Filter dates in range
    result = {}
    for date_str, usage in history[config_key].items():
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            if start_date <= date_obj <= today:
                result[date_str] = usage
        except:
            continue

    # Sort by date
    sorted_result = dict(sorted(result.items()))

    return sorted_result


def get_all_configs_today_usage():
    """
    Get today's usage for all configs.

    Returns:
        dict: Usage data for all configs
            {
                0: {"success": 123, "failed": 5, "total": 128},
                1: {"success": 456, "failed": 2, "total": 458},
                ...
            }
    """
    history = load_history()
    today = get_today_date()

    result = {}

    for config_key, config_history in history.items():
        # Extract config index from "config_N"
        try:
            config_index = int(config_key.split('_')[1])
        except:
            continue

        if today in config_history:
            result[config_index] = config_history[today]
        else:
            result[config_index] = {"success": 0, "failed": 0, "total": 0}

    return result


def cleanup_old_history(keep_days=90):
    """
    Remove history data older than specified days.

    Args:
        keep_days (int): Number of days to keep (default: 90)

    Returns:
        tuple: (int, int) - (total_entries_before, total_entries_after)
    """
    history = load_history()
    cutoff_date = datetime.now() - timedelta(days=keep_days)

    total_before = 0
    total_after = 0

    for config_key in list(history.keys()):
        config_history = history[config_key]
        total_before += len(config_history)

        # Remove old dates
        dates_to_remove = []
        for date_str in config_history.keys():
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if date_obj < cutoff_date:
                    dates_to_remove.append(date_str)
            except:
                continue

        for date_str in dates_to_remove:
            del config_history[date_str]

        total_after += len(config_history)

        # Remove config entirely if no data left
        if len(config_history) == 0:
            del history[config_key]

    save_history(history)

    return (total_before, total_after)


def reset_today_usage(config_index):
    """
    Reset today's usage for a specific config to zero.

    Useful for manual resets or testing.

    Args:
        config_index (int): Index of the config (0-based)

    Returns:
        bool: True if successful
    """
    try:
        history = load_history()
        today = get_today_date()
        config_key = f"config_{config_index}"

        if config_key in history and today in history[config_key]:
            history[config_key][today] = {
                "success": 0,
                "failed": 0,
                "total": 0
            }
            return save_history(history)

        return True

    except Exception as e:
        print(f"Error resetting usage: {e}")
        return False


def get_usage_stats(config_index, days=30):
    """
    Get aggregated statistics for a config over N days.

    Args:
        config_index (int): Index of the config (0-based)
        days (int): Number of days to analyze (default: 30)

    Returns:
        dict: Statistics
            {
                "total_success": 12345,
                "total_failed": 123,
                "total_requests": 12468,
                "avg_daily_success": 411.5,
                "avg_daily_requests": 415.6,
                "success_rate": 99.0,
                "days_tracked": 30
            }
    """
    usage_data = get_usage_range(config_index, days=days)

    if not usage_data:
        return {
            "total_success": 0,
            "total_failed": 0,
            "total_requests": 0,
            "avg_daily_success": 0,
            "avg_daily_requests": 0,
            "success_rate": 0,
            "days_tracked": 0
        }

    total_success = sum(d.get('success', 0) for d in usage_data.values())
    total_failed = sum(d.get('failed', 0) for d in usage_data.values())
    total_requests = total_success + total_failed
    days_tracked = len(usage_data)

    avg_daily_success = total_success / days_tracked if days_tracked > 0 else 0
    avg_daily_requests = total_requests / days_tracked if days_tracked > 0 else 0
    success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0

    return {
        "total_success": total_success,
        "total_failed": total_failed,
        "total_requests": total_requests,
        "avg_daily_success": round(avg_daily_success, 1),
        "avg_daily_requests": round(avg_daily_requests, 1),
        "success_rate": round(success_rate, 2),
        "days_tracked": days_tracked
    }
