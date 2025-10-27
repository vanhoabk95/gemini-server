"""
Proxy Server Dashboard - Main Page

This is the main page of the Streamlit dashboard for monitoring and managing
the proxy server. Use the sidebar to navigate to different pages.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="Proxy Server Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-running {
        color: #00c851;
        font-weight: bold;
    }
    .status-stopped {
        color: #ff4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🌐 Proxy Server Dashboard")
st.markdown("Monitor and manage your proxy server in real-time")

# Helper functions
@st.cache_data(ttl=5)
def load_stats():
    """Load request statistics from JSON file."""
    stats_file = Path('stats/request_stats.json')
    if stats_file.exists():
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            st.error(f"Error loading stats: {e}")
            return None
    return None

@st.cache_data(ttl=5)
def load_proxy_config():
    """Load proxy configuration."""
    config_file = Path('proxy_config.json')
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading config: {e}")
            return None
    return None

@st.cache_data(ttl=5)
def load_gemini_config():
    """Load Gemini configuration."""
    config_file = Path('gemini_config.json')
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return None
    return None

def check_server_running():
    """Check if proxy server is running by testing port connectivity."""
    import socket

    # Try multiple methods to detect if server is running

    # Method 1: Try to connect to the proxy port
    try:
        proxy_config = load_proxy_config()
        port = proxy_config.get('port', 80) if proxy_config else 80

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()

        # If port is open, server is likely running
        if result == 0:
            return True
    except:
        pass

    # Method 2: Check log file freshness (fallback)
    log_file = Path('logs/proxy_server.log')
    if log_file.exists():
        # Check if log was modified in the last 15 minutes (increased from 5)
        modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        time_diff = (datetime.now() - modified_time).total_seconds()
        if time_diff < 900:  # 15 minutes
            return True

    return False

# Main content
col1, col2, col3, col4 = st.columns(4)

# Load data
stats_data = load_stats()
proxy_config = load_proxy_config()
gemini_config = load_gemini_config()
server_running = check_server_running()

# Server Status
with col1:
    st.markdown("### Server Status")
    if server_running:
        st.markdown('<p class="status-running">🟢 Running</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-stopped">🔴 Stopped</p>', unsafe_allow_html=True)

    if proxy_config:
        st.caption(f"Port: {proxy_config.get('port', 'N/A')}")

# Total IPs
with col2:
    st.markdown("### Total IPs")
    if stats_data:
        total_ips = stats_data.get('total_ips', 0)
        st.markdown(f"<h2>{total_ips}</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2>0</h2>", unsafe_allow_html=True)
    st.caption("Unique clients tracked")

# Total Requests
with col3:
    st.markdown("### Total Requests")
    if stats_data:
        total_requests = stats_data.get('total_requests', 0)
        st.markdown(f"<h2>{total_requests:,}</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2>0</h2>", unsafe_allow_html=True)
    st.caption("All time requests")

# Success Rate
with col4:
    st.markdown("### Success Rate")
    if stats_data and stats_data.get('stats'):
        all_stats = stats_data['stats']
        total_success = sum(s.get('success_count', 0) for s in all_stats.values())
        total_failed = sum(s.get('failed_count', 0) for s in all_stats.values())
        total = total_success + total_failed
        if total > 0:
            success_rate = (total_success / total) * 100
            st.markdown(f"<h2>{success_rate:.1f}%</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2>-</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2>-</h2>", unsafe_allow_html=True)
    st.caption("Request success rate")

st.divider()

# Recent Activity Section
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Request Breakdown")
    if stats_data and stats_data.get('stats'):
        all_stats = stats_data['stats']
        total_http = sum(s.get('http_requests', 0) for s in all_stats.values())
        total_https = sum(s.get('https_requests', 0) for s in all_stats.values())
        total_gemini = sum(s.get('gemini_requests', 0) for s in all_stats.values())

        st.metric("HTTP Requests", f"{total_http:,}")
        st.metric("HTTPS Requests", f"{total_https:,}")
        st.metric("Gemini API Requests", f"{total_gemini:,}")
    else:
        st.info("No request data available yet")

with col_right:
    st.subheader("🤖 Gemini API Status")
    if gemini_config:
        # Import tracker here to avoid import at top level
        try:
            import sys
            import os
            sys.path.insert(0, os.path.abspath('.'))
            from proxy.gemini_usage_tracker import get_today_usage
            tracker_available = True
        except:
            tracker_available = False

        if isinstance(gemini_config, list):
            configs = gemini_config
        elif isinstance(gemini_config, dict) and 'configs' in gemini_config:
            configs = gemini_config['configs']
        else:
            configs = [gemini_config]

        st.metric("Total Configs", len(configs))

        # Count status
        healthy = sum(1 for c in configs if c.get('status') == 'healthy')
        failed = sum(1 for c in configs if c.get('status') in ['failed', 'timeout', 'rate_limited'])

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("🟢 Healthy", healthy)
        with col_b:
            st.metric("🔴 Failed", failed)

        # Daily usage
        if tracker_available:
            st.markdown("**Today's Usage:**")
            for idx, cfg in enumerate(configs):
                today_usage = get_today_usage(idx)
                limit = cfg.get('daily_limit', 1000)
                success = today_usage.get('success', 0)
                usage_pct = (success / limit * 100) if limit > 0 else 0

                st.markdown(f"Config #{idx + 1}: {success:,} / {limit:,}")
                st.progress(min(usage_pct / 100, 1.0))
    else:
        st.info("Gemini API not configured")

st.divider()

# System Info
st.subheader("ℹ️ System Information")
col_sys1, col_sys2, col_sys3 = st.columns(3)

with col_sys1:
    if proxy_config:
        st.write("**Proxy Configuration:**")
        st.write(f"- Host: `{proxy_config.get('host', 'N/A')}`")
        st.write(f"- Port: `{proxy_config.get('port', 'N/A')}`")
        st.write(f"- Max Connections: `{proxy_config.get('max_connections', 'N/A')}`")

with col_sys2:
    if proxy_config:
        st.write("**Logging:**")
        st.write(f"- Level: `{proxy_config.get('log_level', 'N/A')}`")
        st.write(f"- Directory: `{proxy_config.get('log_dir', 'N/A')}`")
        st.write(f"- File Logging: `{proxy_config.get('enable_file_logging', 'N/A')}`")

with col_sys3:
    if stats_data:
        st.write("**Statistics:**")
        generated_at = stats_data.get('generated_at', 'Unknown')
        if generated_at != 'Unknown':
            try:
                dt = datetime.fromisoformat(generated_at)
                generated_at = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        st.write(f"- Last Updated: `{generated_at}`")
        st.write(f"- Stats Directory: `{proxy_config.get('stats_dir', 'stats') if proxy_config else 'stats'}`")

# Auto-refresh option
st.divider()
col_refresh1, col_refresh2 = st.columns([1, 3])
with col_refresh1:
    if st.button("🔄 Refresh Data", width='stretch'):
        st.cache_data.clear()
        st.rerun()

with col_refresh2:
    st.info("💡 Use the sidebar to navigate to different sections: Statistics, Gemini Config, Logs, and Settings")

# Footer
st.divider()
st.caption("Proxy Server Dashboard v1.0 | Built with Streamlit")
