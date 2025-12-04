"""
Gemini API Gateway Dashboard - Main Page

Monitor and manage your Gemini API gateway in real-time.
"""

import sys
import os

# Add parent directory to path FIRST
sys.path.insert(0, os.path.abspath('.'))

import json
from pathlib import Path
from datetime import datetime
from copy import deepcopy

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from proxy.gemini_usage_tracker import get_today_usage, get_usage_range
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Gemini API Gateway Dashboard",
    page_icon="🤖",
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
st.title("🤖 Gemini API Gateway Dashboard")
st.markdown("Monitor and manage your Gemini API gateway in real-time")

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

def save_gemini_config(config_data):
    """Save Gemini configuration to JSON file."""
    config_file = Path('gemini_config.json')
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

def check_server_running():
    """Check if gateway server is running by monitoring log file activity."""
    # Check log file freshness - if log was recently modified, server is likely running
    log_file = Path('logs/proxy_server.log')
    if log_file.exists():
        try:
            modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            time_diff = (datetime.now() - modified_time).total_seconds()
            # If log was modified in the last 5 minutes, server is running
            if time_diff < 300:  # 5 minutes
                return True
        except:
            pass

    return False

# Load data
stats_data = load_stats()
proxy_config = load_proxy_config()
gemini_config = load_gemini_config()
server_running = check_server_running()

# Parse Gemini configs (make a deep copy to avoid modifying cached data)
if gemini_config:
    if isinstance(gemini_config, list):
        configs = deepcopy(gemini_config)
    elif isinstance(gemini_config, dict) and 'configs' in gemini_config:
        configs = deepcopy(gemini_config['configs'])
    else:
        configs = [deepcopy(gemini_config)]
else:
    configs = []

# ============================================================================
# TOP METRICS
# ============================================================================
st.subheader("📈 Overview")
col1, col2, col3, col4 = st.columns(4)

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

# ============================================================================
# GEMINI API CONFIGURATIONS
# ============================================================================
st.subheader("🤖 Gemini API Configurations")

if configs:
    # Configuration metrics
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)

    with col_c1:
        st.metric("Total Configs", len(configs))
    with col_c2:
        healthy = sum(1 for c in configs if c.get('status') == 'healthy')
        st.metric("🟢 Healthy", healthy)
    with col_c3:
        failed = sum(1 for c in configs if c.get('status') in ['failed', 'timeout', 'rate_limited'])
        st.metric("🔴 Failed", failed)
    with col_c4:
        unknown = sum(1 for c in configs if c.get('status') in ['unknown', None])
        st.metric("⚪ Unknown", unknown)

    # Today's usage if tracker available
    if TRACKER_AVAILABLE:
        st.markdown("**Today's Usage:**")

        total_success_today = 0
        total_failed_today = 0

        for idx in range(len(configs)):
            today_usage = get_today_usage(idx)
            total_success_today += today_usage.get('success', 0)
            total_failed_today += today_usage.get('failed', 0)

        total_today = total_success_today + total_failed_today

        col_u1, col_u2, col_u3, col_u4 = st.columns(4)
        with col_u1:
            st.metric("Requests Today", f"{total_today:,}")
        with col_u2:
            st.metric("✅ Success", f"{total_success_today:,}")
        with col_u3:
            st.metric("❌ Failed", f"{total_failed_today:,}")
        with col_u4:
            success_rate_today = (total_success_today / total_today * 100) if total_today > 0 else 0
            st.metric("Success Rate", f"{success_rate_today:.1f}%")

    # Configuration details table
    st.markdown("**Configuration Details:**")
    config_list = []
    for idx, cfg in enumerate(configs):
        status_emoji = {
            'healthy': '🟢',
            'failed': '🔴',
            'timeout': '🟠',
            'rate_limited': '🟡',
            'unknown': '⚪'
        }.get(cfg.get('status'), '⚪')

        if TRACKER_AVAILABLE:
            today = get_today_usage(idx)
            today_requests = today.get('success', 0) + today.get('failed', 0)
        else:
            today_requests = 'N/A'

        # Get API key
        api_key = cfg.get('api_key', '')
        api_key_display = f"***{api_key[-8:]}" if api_key and len(api_key) > 8 else 'N/A'

        # Get error message
        error_msg = cfg.get('error_message', '')
        error_display = error_msg if error_msg else '-'

        config_list.append({
            'ID': f"#{idx + 1}",
            'Status': f"{status_emoji} {cfg.get('status', 'unknown')}",
            'Model': cfg.get('model', 'N/A'),
            'Daily Limit': cfg.get('daily_limit', 'N/A'),
            'Today Requests': today_requests,
            'API Key': api_key_display,
            'Error Message': error_display
        })

    df_configs = pd.DataFrame(config_list)
    st.dataframe(df_configs, width='stretch', hide_index=True)

    # Configuration Management
    st.markdown("**Manage Configurations:**")

    col_add, col_edit = st.columns(2)

    with col_add:
        with st.expander("➕ Add New Configuration", expanded=True):
            with st.form("add_config_form"):
                st.write("Add a new Gemini API configuration:")
                new_api_key = st.text_input("API Key", type="password", key="new_api_key")
                new_model = st.text_input("Model", value="gemini-2.0-flash-exp", key="new_model")
                new_daily_limit = st.number_input("Daily Limit", min_value=1, value=1000, key="new_limit")

                submitted = st.form_submit_button("Add Configuration")
                if submitted:
                    if not new_api_key:
                        st.error("API Key is required!")
                    else:
                        # Create new config
                        new_config = {
                            "api_key": new_api_key,
                            "model": new_model,
                            "daily_limit": new_daily_limit,
                            "status": "unknown"
                        }

                        # Add to configs list
                        configs.append(new_config)

                        # Save to file
                        save_data = {"configs": configs}
                        if save_gemini_config(save_data):
                            st.success("✅ Configuration added successfully!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Failed to save configuration")

    with col_edit:
        with st.expander("✏️ Edit/Delete Configuration", expanded=True):
            if len(configs) > 0:
                config_options = [f"Config #{i+1} - {cfg.get('model', 'N/A')}" for i, cfg in enumerate(configs)]
                selected_config_idx = st.selectbox("Select Configuration", range(len(configs)), format_func=lambda x: config_options[x], key="config_selector")

                selected_cfg = configs[selected_config_idx]

                # Use a unique form key based on selected index to force re-render
                with st.form(f"edit_config_form_{selected_config_idx}"):
                    st.write(f"Edit Configuration #{selected_config_idx + 1}:")
                    edit_api_key = st.text_input("API Key", value=selected_cfg.get('api_key', ''))
                    edit_model = st.text_input("Model", value=selected_cfg.get('model', ''))
                    edit_daily_limit = st.number_input("Daily Limit", min_value=1, value=selected_cfg.get('daily_limit', 1000))

                    col_save, col_delete = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
                    with col_delete:
                        delete_btn = st.form_submit_button("🗑️ Delete", use_container_width=True)

                    if save_btn:
                        # Preserve all existing fields and only update the ones we're editing
                        updated_config = deepcopy(selected_cfg)

                        # Update fields
                        updated_config['api_key'] = edit_api_key
                        updated_config['model'] = edit_model
                        updated_config['daily_limit'] = edit_daily_limit

                        configs[selected_config_idx] = updated_config

                        save_data = {"configs": configs}
                        if save_gemini_config(save_data):
                            st.success("✅ Configuration updated successfully!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Failed to save configuration")

                    if delete_btn:
                        # Delete config
                        configs.pop(selected_config_idx)
                        save_data = {"configs": configs}
                        if save_gemini_config(save_data):
                            st.success("✅ Configuration deleted successfully!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Failed to delete configuration")
            else:
                st.info("No configurations available to edit")

    # Usage trends chart
    if TRACKER_AVAILABLE:
        st.markdown("**Usage Trends (Last 30 Days):**")

        all_lines_data = {}
        for idx, cfg in enumerate(configs):
            usage_data = get_usage_range(idx, days=30)
            if usage_data:
                all_lines_data[f"Config #{idx + 1}"] = usage_data

        if all_lines_data:
            fig = go.Figure()

            for config_name, usage_data in all_lines_data.items():
                dates = list(usage_data.keys())
                success_counts = [d['success'] for d in usage_data.values()]

                fig.add_trace(go.Scatter(
                    name=config_name,
                    x=dates,
                    y=success_counts,
                    mode='lines+markers',
                    line=dict(width=2),
                    marker=dict(size=6)
                ))

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Successful Requests",
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig)
        else:
            st.info("No usage data available yet")

else:
    st.info("Gemini API not configured. Add your first configuration below:")

    with st.expander("➕ Add First Configuration", expanded=True):
        with st.form("add_first_config_form"):
            st.write("Add a new Gemini API configuration:")
            new_api_key = st.text_input("API Key", type="password", key="first_api_key")
            new_model = st.text_input("Model", value="gemini-2.0-flash-exp", key="first_model")
            new_daily_limit = st.number_input("Daily Limit", min_value=1, value=1000, key="first_limit")

            submitted = st.form_submit_button("Add Configuration")
            if submitted:
                if not new_api_key:
                    st.error("API Key is required!")
                else:
                    # Create new config
                    new_config = {
                        "api_key": new_api_key,
                        "model": new_model,
                        "daily_limit": new_daily_limit,
                        "status": "unknown"
                    }

                    # Save to file
                    save_data = {"configs": [new_config]}
                    if save_gemini_config(save_data):
                        st.success("✅ Configuration added successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Failed to save configuration")

st.divider()

# ============================================================================
# REQUEST STATISTICS
# ============================================================================
st.subheader("📊 Request Statistics")

if stats_data and stats_data.get('stats'):
    all_stats = stats_data['stats']

    # Top 10 IPs chart
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("**Top 10 IPs by Request Count:**")
        top_ips = sorted(
            all_stats.items(),
            key=lambda x: x[1].get('total_requests', 0),
            reverse=True
        )[:10]

        if top_ips:
            top_ips_data = {
                'IP Address': [ip for ip, _ in top_ips],
                'Total Requests': [stats.get('total_requests', 0) for _, stats in top_ips]
            }
            df_top_ips = pd.DataFrame(top_ips_data)

            fig_bar = px.bar(
                df_top_ips,
                x='Total Requests',
                y='IP Address',
                orientation='h',
                color='Total Requests',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(
                height=400,
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_bar)
        else:
            st.info("No IP data available")

    with col_chart2:
        st.markdown("**Success vs Failed Requests:**")
        total_success = sum(s.get('success_count', 0) for s in all_stats.values())
        total_failed = sum(s.get('failed_count', 0) for s in all_stats.values())

        success_data = {
            'Status': ['Success', 'Failed'],
            'Count': [total_success, total_failed]
        }
        df_success = pd.DataFrame(success_data)

        fig_pie = px.pie(
            df_success,
            values='Count',
            names='Status',
            color='Status',
            color_discrete_map={'Success': '#00CC96', 'Failed': '#EF553B'},
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie)

    # Detailed IP Statistics Table
    st.markdown("**Detailed IP Statistics:**")

    ip_list = []
    for ip, stats in all_stats.items():
        ip_list.append({
            'IP Address': ip,
            'Total Requests': stats.get('total_requests', 0),
            'Success': stats.get('success_count', 0),
            'Failed': stats.get('failed_count', 0),
            'Success Rate': f"{(stats.get('success_count', 0) / stats.get('total_requests', 1) * 100):.1f}%",
            'First Seen': stats.get('first_seen', 'N/A'),
            'Last Seen': stats.get('last_seen', 'N/A')
        })

    df_ips = pd.DataFrame(ip_list)
    df_ips = df_ips.sort_values('Total Requests', ascending=False)

    st.dataframe(df_ips, width='stretch', hide_index=True)

else:
    st.info("No request data available yet. Make sure the gateway server is running and has processed some requests.")

st.divider()

# ============================================================================
# SYSTEM INFORMATION
# ============================================================================
st.subheader("ℹ️ System Information")
col_sys1, col_sys2, col_sys3 = st.columns(3)

with col_sys1:
    if proxy_config:
        st.write("**Gateway Configuration:**")
        st.write(f"- Host: `{proxy_config.get('host', 'N/A')}`")
        st.write(f"- Port: `{proxy_config.get('port', 'N/A')}`")
        st.write(f"- Log Level: `{proxy_config.get('log_level', 'N/A')}`")

with col_sys2:
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
        st.write(f"- Total IPs: `{stats_data.get('total_ips', 0)}`")
        st.write(f"- Total Requests: `{stats_data.get('total_requests', 0):,}`")

with col_sys3:
    st.write("**Quick Actions:**")
    if st.button("🔄 Refresh Data", width='stretch'):
        st.cache_data.clear()
        st.rerun()
    st.write("- View Logs → Use sidebar")
    st.write("- Edit Config → See above ⬆️")

# Footer
st.divider()
st.caption("Gemini API Gateway Dashboard | Built with Streamlit")
