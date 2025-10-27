"""
Gemini Manager Page - Manage Gemini API Configurations

View, add, edit, and delete Gemini API configurations.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Add parent directory to path to import proxy modules
sys.path.insert(0, os.path.abspath('.'))

from proxy.gemini_usage_tracker import (
    get_today_usage,
    get_usage_range,
    get_usage_stats,
    reset_today_usage
)
import plotly.graph_objects as go

st.set_page_config(
    page_title="Gemini Manager - Proxy Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Gemini API Manager")
st.markdown("Manage Google Gemini API configurations with automatic failover support")

# Helper functions
def load_gemini_config():
    """Load Gemini configuration from JSON file."""
    config_file = Path('gemini_config.json')
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            st.error(f"Error loading Gemini config: {e}")
            return None
    return None

def save_gemini_config(config_data):
    """Save Gemini configuration to JSON file."""
    config_file = Path('gemini_config.json')
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving Gemini config: {e}")
        return False

def mask_api_key(api_key):
    """Mask API key for display."""
    if not api_key:
        return "Not set"
    if len(api_key) <= 4:
        return "***"
    return f"***{api_key[-4:]}"

def get_status_emoji(status):
    """Get emoji for config status."""
    status_map = {
        'healthy': '🟢',
        'failed': '🔴',
        'timeout': '🟡',
        'rate_limited': '🟡',
        'server_error': '🔴',
        'connection_error': '🔴',
        'unknown': '⚪'
    }
    return status_map.get(status, '⚪')

# Load config
config_data = load_gemini_config()

if config_data is None:
    st.warning("⚠️ Gemini configuration file not found")
    st.info("💡 Create a new configuration below to get started")
    configs = []
else:
    # Parse config format
    if isinstance(config_data, list):
        configs = config_data
    elif isinstance(config_data, dict):
        if 'configs' in config_data:
            configs = config_data['configs']
        else:
            # Single config object
            configs = [config_data]
    else:
        st.error("Invalid config format")
        configs = []

# Display summary
st.subheader("📊 Configuration Summary")

# Status metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Configs", len(configs))
with col2:
    healthy_count = sum(1 for c in configs if c.get('status') == 'healthy')
    st.metric("🟢 Healthy", healthy_count)
with col3:
    failed_count = sum(1 for c in configs if c.get('status') in ['failed', 'timeout', 'rate_limited', 'server_error', 'connection_error'])
    st.metric("🔴 Failed", failed_count)
with col4:
    unknown_count = sum(1 for c in configs if c.get('status') == 'unknown' or c.get('status') is None)
    st.metric("⚪ Unknown", unknown_count)

# Usage metrics (today)
if configs:
    st.markdown("**Today's Usage Summary:**")
    col_u1, col_u2, col_u3, col_u4 = st.columns(4)

    total_success_today = 0
    total_failed_today = 0
    total_limit = 0

    for idx in range(len(configs)):
        today_usage = get_today_usage(idx)
        total_success_today += today_usage.get('success', 0)
        total_failed_today += today_usage.get('failed', 0)
        total_limit += configs[idx].get('daily_limit', 1000)

    total_today = total_success_today + total_failed_today

    with col_u1:
        st.metric("Total Requests Today", f"{total_today:,}")
    with col_u2:
        st.metric("✅ Success", f"{total_success_today:,}")
    with col_u3:
        st.metric("❌ Failed", f"{total_failed_today:,}")
    with col_u4:
        success_rate = (total_success_today / total_today * 100) if total_today > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")

st.divider()

# Display existing configs
if configs:
    st.subheader("🔑 API Key Configurations")

    for idx, config in enumerate(configs):
        with st.expander(f"Config #{idx + 1} - {mask_api_key(config.get('google_api_key'))}"):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                # Display config info
                status = config.get('status', 'unknown')
                status_emoji = get_status_emoji(status)

                st.markdown(f"**Status:** {status_emoji} {status}")
                st.markdown(f"**API Key:** `{mask_api_key(config.get('google_api_key'))}`")
                st.markdown(f"**Model:** `{config.get('model', 'gemini-1.5-flash')}`")
                st.markdown(f"**API Base:** `{config.get('api_base', 'https://generativelanguage.googleapis.com')}`")

                if config.get('last_check'):
                    try:
                        last_check = datetime.fromisoformat(config['last_check'])
                        last_check_str = last_check.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        last_check_str = config['last_check']
                    st.markdown(f"**Last Check:** {last_check_str}")

                if config.get('error_message'):
                    st.warning(f"⚠️ Error: {config['error_message']}")

                # Display usage statistics
                st.markdown("---")
                st.markdown("**Daily Usage (Today):**")

                today_usage = get_today_usage(idx)
                daily_limit = config.get('daily_limit', 1000)
                success_count = today_usage.get('success', 0)
                failed_count = today_usage.get('failed', 0)
                total_count = today_usage.get('total', 0)

                usage_percent = (success_count / daily_limit * 100) if daily_limit > 0 else 0

                # Progress bar
                st.markdown(f"**Success:** {success_count:,} / {daily_limit:,} ({usage_percent:.1f}%)")
                st.progress(min(usage_percent / 100, 1.0))

                # Warning if near limit
                if usage_percent >= 90:
                    st.error(f"⚠️ Warning: {usage_percent:.1f}% of daily limit reached!")
                elif usage_percent >= 80:
                    st.warning(f"⚠️ Caution: {usage_percent:.1f}% of daily limit used")

                # Usage details
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("Success", f"{success_count:,}")
                with col_stat2:
                    st.metric("Failed", f"{failed_count:,}")
                with col_stat3:
                    if total_count > 0:
                        success_rate = (success_count / total_count * 100)
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    else:
                        st.metric("Success Rate", "N/A")

            with col_actions:
                st.markdown("**Actions:**")

                # Edit button
                if st.button("✏️ Edit", key=f"edit_{idx}", width='stretch'):
                    st.session_state[f'editing_{idx}'] = True
                    st.rerun()

                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{idx}", width='stretch'):
                    if st.session_state.get(f'confirm_delete_{idx}'):
                        # Confirmed delete
                        configs.pop(idx)
                        if save_gemini_config(configs):
                            st.success(f"✅ Config #{idx + 1} deleted successfully!")
                            st.session_state.pop(f'confirm_delete_{idx}')
                            st.rerun()
                    else:
                        # Ask for confirmation
                        st.session_state[f'confirm_delete_{idx}'] = True
                        st.rerun()

                # Show confirm delete message
                if st.session_state.get(f'confirm_delete_{idx}'):
                    st.error("⚠️ Confirm delete?")
                    if st.button("Cancel", key=f"cancel_delete_{idx}", width='stretch'):
                        st.session_state.pop(f'confirm_delete_{idx}')
                        st.rerun()

            # Edit form
            if st.session_state.get(f'editing_{idx}'):
                st.markdown("---")
                st.markdown("**Edit Configuration:**")

                with st.form(key=f"edit_form_{idx}"):
                    new_api_key = st.text_input(
                        "Google API Key",
                        value=config.get('google_api_key', ''),
                        type="password",
                        help="Your Google API key for Gemini"
                    )
                    new_model = st.text_input(
                        "Model",
                        value=config.get('model', 'gemini-1.5-flash'),
                        help="Gemini model name (e.g., gemini-1.5-flash, gemini-1.5-pro)"
                    )
                    new_api_base = st.text_input(
                        "API Base URL",
                        value=config.get('api_base', 'https://generativelanguage.googleapis.com'),
                        help="Google API base URL"
                    )
                    new_daily_limit = st.number_input(
                        "Daily Limit (requests/day)",
                        min_value=0,
                        max_value=1000000,
                        value=config.get('daily_limit', 1000),
                        help="Reference limit for daily request tracking (not enforced)"
                    )

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button("💾 Save Changes", width='stretch')
                    with col_cancel:
                        cancel = st.form_submit_button("❌ Cancel", width='stretch')

                    if submitted:
                        # Update config
                        configs[idx]['google_api_key'] = new_api_key
                        configs[idx]['model'] = new_model
                        configs[idx]['api_base'] = new_api_base
                        configs[idx]['daily_limit'] = new_daily_limit

                        if save_gemini_config(configs):
                            st.success("✅ Configuration updated successfully!")
                            st.session_state.pop(f'editing_{idx}')
                            st.rerun()

                    if cancel:
                        st.session_state.pop(f'editing_{idx}')
                        st.rerun()

            # Usage history chart
            st.markdown("---")
            st.markdown("**📈 Usage History (Last 30 Days)**")

            usage_data = get_usage_range(idx, days=30)

            if usage_data and len(usage_data) > 0:
                dates = list(usage_data.keys())
                success_counts = [d['success'] for d in usage_data.values()]
                failed_counts = [d['failed'] for d in usage_data.values()]

                fig = go.Figure()

                # Add success bars
                fig.add_trace(go.Bar(
                    name='Success',
                    x=dates,
                    y=success_counts,
                    marker_color='lightgreen'
                ))

                # Add failed bars
                fig.add_trace(go.Bar(
                    name='Failed',
                    x=dates,
                    y=failed_counts,
                    marker_color='lightcoral'
                ))

                # Add daily limit line
                daily_limit = config.get('daily_limit', 1000)
                fig.add_trace(go.Scatter(
                    name='Daily Limit',
                    x=dates,
                    y=[daily_limit] * len(dates),
                    mode='lines',
                    line=dict(color='orange', dash='dash', width=2)
                ))

                fig.update_layout(
                    barmode='stack',
                    height=350,
                    xaxis_title="Date",
                    yaxis_title="Requests",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    margin=dict(l=0, r=0, t=30, b=0)
                )

                st.plotly_chart(fig)

                # Show 30-day stats
                stats_30d = get_usage_stats(idx, days=30)
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("Avg Daily Success", f"{stats_30d['avg_daily_success']:.0f}")
                with col_s2:
                    st.metric("30-Day Total", f"{stats_30d['total_requests']:,}")
                with col_s3:
                    st.metric("30-Day Success Rate", f"{stats_30d['success_rate']:.1f}%")
            else:
                st.info("No usage history available yet")

    st.divider()

# Add new config section
st.subheader("➕ Add New Configuration")

with st.form(key="add_config_form"):
    st.markdown("Add a new Google API key for failover support")

    new_api_key = st.text_input(
        "Google API Key *",
        type="password",
        help="Your Google API key for Gemini"
    )
    new_model = st.text_input(
        "Model",
        value="gemini-1.5-flash",
        help="Gemini model name (e.g., gemini-1.5-flash, gemini-1.5-pro)"
    )
    new_api_base = st.text_input(
        "API Base URL",
        value="https://generativelanguage.googleapis.com",
        help="Google API base URL"
    )
    new_daily_limit = st.number_input(
        "Daily Limit (requests/day)",
        min_value=0,
        max_value=1000000,
        value=1000,
        help="Reference limit for daily request tracking (not enforced)"
    )

    submitted = st.form_submit_button("➕ Add Configuration", width='stretch')

    if submitted:
        if not new_api_key:
            st.error("❌ API Key is required")
        else:
            # Create new config
            new_config = {
                'google_api_key': new_api_key,
                'model': new_model,
                'api_base': new_api_base,
                'daily_limit': new_daily_limit,
                'enabled': True,
                'status': 'unknown',
                'last_check': None,
                'error_message': None
            }

            configs.append(new_config)

            if save_gemini_config(configs):
                st.success("✅ New configuration added successfully!")
                st.balloons()
                st.rerun()

st.divider()

# Info and tips
st.info("""
ℹ️ **Important Notes:**

- **Automatic Failover:** The proxy will automatically switch to the next config if one fails
- **Status Tracking:** Config status is updated in real-time by the proxy server
- **Restart Required:** After making changes, restart the proxy server to apply them
- **API Key Security:** API keys are stored in `gemini_config.json` - keep this file secure!

💡 **Tips:**
- Add multiple API keys for better reliability and rate limit handling
- Use different models (flash/pro) based on your needs
- Monitor the status regularly to ensure all configs are healthy
""")

# Refresh button
if st.button("🔄 Refresh Status", width='stretch'):
    st.rerun()
