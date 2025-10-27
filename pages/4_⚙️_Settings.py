"""
Settings Page - Proxy Configuration Editor

Edit proxy server configuration settings.
"""

import json
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Settings - Proxy Dashboard",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Proxy Server Settings")
st.markdown("Configure proxy server parameters")

# Helper functions
def load_config():
    """Load proxy configuration from JSON file."""
    config_file = Path('proxy_config.json')
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading config: {e}")
            return None
    return None

def save_config(config_data):
    """Save proxy configuration to JSON file."""
    config_file = Path('proxy_config.json')
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

def validate_config(config):
    """Validate configuration values."""
    errors = []

    # Validate port
    port = config.get('port')
    if not isinstance(port, int) or port < 1 or port > 65535:
        errors.append("Port must be between 1 and 65535")

    # Validate max_connections
    max_conn = config.get('max_connections')
    if not isinstance(max_conn, int) or max_conn < 1:
        errors.append("Max connections must be a positive integer")

    # Validate log_level
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.get('log_level') not in valid_levels:
        errors.append(f"Log level must be one of: {', '.join(valid_levels)}")

    # Validate stats_auto_save_interval
    interval = config.get('stats_auto_save_interval')
    if not isinstance(interval, int) or interval < 0:
        errors.append("Stats auto-save interval must be a non-negative integer")

    return errors

# Default values
DEFAULT_CONFIG = {
    'host': '0.0.0.0',
    'port': 80,
    'max_connections': 1000,
    'log_level': 'INFO',
    'log_dir': 'logs',
    'enable_file_logging': True,
    'stats_dir': 'stats',
    'stats_auto_save_interval': 60
}

# Load current config
current_config = load_config()

if current_config is None:
    st.warning("⚠️ Configuration file not found. Using default values.")
    current_config = DEFAULT_CONFIG.copy()

# Initialize session state for editing
if 'config_edited' not in st.session_state:
    st.session_state.config_edited = current_config.copy()

# Configuration form
st.subheader("🔧 Proxy Configuration")

with st.form(key="config_form"):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Network Settings**")

        host = st.text_input(
            "Host",
            value=st.session_state.config_edited.get('host', '0.0.0.0'),
            help="IP address to bind the proxy server (0.0.0.0 for all interfaces)"
        )

        port = st.number_input(
            "Port",
            min_value=1,
            max_value=65535,
            value=st.session_state.config_edited.get('port', 80),
            help="Port number for the proxy server"
        )

        max_connections = st.number_input(
            "Max Connections",
            min_value=1,
            max_value=100000,
            value=st.session_state.config_edited.get('max_connections', 1000),
            help="Maximum number of simultaneous connections"
        )

    with col2:
        st.markdown("**Logging Settings**")

        log_level = st.selectbox(
            "Log Level",
            options=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            index=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].index(
                st.session_state.config_edited.get('log_level', 'INFO')
            ),
            help="Logging verbosity level"
        )

        log_dir = st.text_input(
            "Log Directory",
            value=st.session_state.config_edited.get('log_dir', 'logs'),
            help="Directory to store log files"
        )

        enable_file_logging = st.checkbox(
            "Enable File Logging",
            value=st.session_state.config_edited.get('enable_file_logging', True),
            help="Enable writing logs to files (with daily rotation)"
        )

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Statistics Settings**")

        stats_dir = st.text_input(
            "Stats Directory",
            value=st.session_state.config_edited.get('stats_dir', 'stats'),
            help="Directory to store request statistics"
        )

    with col4:
        st.markdown("**Auto-save Settings**")

        stats_auto_save_interval = st.number_input(
            "Stats Auto-save Interval (seconds)",
            min_value=0,
            max_value=3600,
            value=st.session_state.config_edited.get('stats_auto_save_interval', 60),
            help="How often to auto-save statistics (0 to disable)"
        )

    st.markdown("---")

    # Action buttons
    col_save, col_reset, col_default = st.columns(3)

    with col_save:
        save_button = st.form_submit_button("💾 Save Configuration", width='stretch')

    with col_reset:
        reset_button = st.form_submit_button("↩️ Reset to Current", width='stretch')

    with col_default:
        default_button = st.form_submit_button("🔄 Restore Defaults", width='stretch')

    # Handle form submission
    if save_button:
        # Create new config
        new_config = {
            'host': host,
            'port': port,
            'max_connections': max_connections,
            'log_level': log_level,
            'log_dir': log_dir,
            'enable_file_logging': enable_file_logging,
            'stats_dir': stats_dir,
            'stats_auto_save_interval': stats_auto_save_interval
        }

        # Validate
        errors = validate_config(new_config)

        if errors:
            st.error("❌ Configuration validation failed:")
            for error in errors:
                st.error(f"  • {error}")
        else:
            # Save config
            if save_config(new_config):
                st.success("✅ Configuration saved successfully!")
                st.session_state.config_edited = new_config
                st.balloons()
                st.warning("⚠️ **Restart the proxy server** to apply changes")
            else:
                st.error("❌ Failed to save configuration")

    if reset_button:
        # Reset to current saved config
        st.session_state.config_edited = current_config.copy()
        st.info("↩️ Configuration reset to current saved values")
        st.rerun()

    if default_button:
        # Reset to defaults
        st.session_state.config_edited = DEFAULT_CONFIG.copy()
        st.info("🔄 Configuration reset to default values")
        st.rerun()

st.divider()

# Configuration preview
st.subheader("👁️ Current Configuration Preview")

col_preview1, col_preview2 = st.columns(2)

with col_preview1:
    st.markdown("**Network Settings**")
    st.json({
        'host': current_config.get('host'),
        'port': current_config.get('port'),
        'max_connections': current_config.get('max_connections')
    })

    st.markdown("**Statistics Settings**")
    st.json({
        'stats_dir': current_config.get('stats_dir'),
        'stats_auto_save_interval': current_config.get('stats_auto_save_interval')
    })

with col_preview2:
    st.markdown("**Logging Settings**")
    st.json({
        'log_level': current_config.get('log_level'),
        'log_dir': current_config.get('log_dir'),
        'enable_file_logging': current_config.get('enable_file_logging')
    })

st.divider()

# Configuration file info
st.subheader("📄 Configuration File")
config_file = Path('proxy_config.json')

if config_file.exists():
    col_file1, col_file2 = st.columns([2, 1])

    with col_file1:
        st.code(config_file.read_text(encoding='utf-8'), language='json')

    with col_file2:
        st.metric("File Size", f"{config_file.stat().st_size} bytes")
        st.caption(f"Location: `{config_file.absolute()}`")

        # Download button
        st.download_button(
            label="📥 Download Config",
            data=config_file.read_text(encoding='utf-8'),
            file_name='proxy_config.json',
            mime='application/json',
            width='stretch'
        )

st.divider()

# Tips and warnings
st.info("""
ℹ️ **Configuration Tips:**

**Network Settings:**
- Use `0.0.0.0` to listen on all interfaces, or specify a specific IP
- Port 80 requires admin/root privileges on most systems
- Consider using port 8080 or higher for non-privileged operation
- Max connections should be tuned based on your system resources

**Logging Settings:**
- DEBUG level provides detailed information but generates large log files
- INFO level is recommended for production use
- File logging includes automatic daily rotation keeping 30 days of logs

**Statistics Settings:**
- Stats are automatically saved to JSON files
- Lower auto-save intervals provide more real-time data but may impact performance
- Set interval to 0 to disable auto-save (manual save only)

⚠️ **Important:**
- Changes require restarting the proxy server
- Keep the configuration file secure
- Backup your configuration before making major changes
""")

# Restart instructions
st.warning("""
🔄 **To Apply Changes:**

1. Stop the proxy server (Ctrl+C in the terminal)
2. Verify the configuration changes
3. Restart the proxy server: `python main.py`
4. Refresh this dashboard to verify the changes
""")
