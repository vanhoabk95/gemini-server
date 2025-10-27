"""
Logs Viewer Page - View and Search Log Files

Browse, search, and filter proxy server log files.
"""

import re
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Logs Viewer - Proxy Dashboard",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Logs Viewer")
st.markdown("View and search proxy server log files")

# Helper functions
@st.cache_data(ttl=5)
def get_log_files():
    """Get list of log files in logs directory."""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        return []

    log_files = sorted(
        logs_dir.glob('*.log*'),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    return log_files

def read_log_file(file_path, max_lines=None, from_end=False):
    """Read log file content."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            if from_end and max_lines:
                # Read last N lines
                lines = f.readlines()
                return lines[-max_lines:]
            elif max_lines:
                # Read first N lines
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                return lines
            else:
                # Read all lines
                return f.readlines()
    except Exception as e:
        st.error(f"Error reading log file: {e}")
        return []

def filter_logs(lines, log_level=None, keyword=None):
    """Filter log lines by level and keyword."""
    filtered = []

    for line in lines:
        # Filter by log level
        if log_level and log_level != "ALL":
            if f" - {log_level} - " not in line:
                continue

        # Filter by keyword
        if keyword:
            if keyword.lower() not in line.lower():
                continue

        filtered.append(line)

    return filtered

def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def highlight_log_level(line):
    """Add color highlighting to log levels."""
    if " - DEBUG - " in line:
        return line.replace(" - DEBUG - ", " - <span style='color: #888888; font-weight: bold;'>DEBUG</span> - ")
    elif " - INFO - " in line:
        return line.replace(" - INFO - ", " - <span style='color: #0066ff; font-weight: bold;'>INFO</span> - ")
    elif " - WARNING - " in line:
        return line.replace(" - WARNING - ", " - <span style='color: #ff9900; font-weight: bold;'>WARNING</span> - ")
    elif " - ERROR - " in line:
        return line.replace(" - ERROR - ", " - <span style='color: #ff0000; font-weight: bold;'>ERROR</span> - ")
    elif " - CRITICAL - " in line:
        return line.replace(" - CRITICAL - ", " - <span style='color: #cc0000; font-weight: bold;'>CRITICAL</span> - ")
    return line

# Get log files
log_files = get_log_files()

if not log_files:
    st.warning("⚠️ No log files found in the 'logs' directory")
    st.info("💡 Make sure the proxy server is running with file logging enabled")
    st.stop()

# File selector
st.subheader("📁 Select Log File")
col_file, col_info = st.columns([2, 1])

with col_file:
    selected_file_idx = st.selectbox(
        "Log File",
        range(len(log_files)),
        format_func=lambda x: log_files[x].name,
        label_visibility="collapsed"
    )
    selected_file = log_files[selected_file_idx]

with col_info:
    file_stat = selected_file.stat()
    st.metric("File Size", format_file_size(file_stat.st_size))
    modified_time = datetime.fromtimestamp(file_stat.st_mtime)
    st.caption(f"Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

st.divider()

# Filter controls
st.subheader("🔍 Filters")
col_level, col_keyword, col_mode = st.columns([1, 2, 1])

with col_level:
    log_level = st.selectbox(
        "Log Level",
        options=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )

with col_keyword:
    keyword = st.text_input(
        "Search Keyword",
        placeholder="Enter keyword to search...",
        help="Case-insensitive search"
    )

with col_mode:
    view_mode = st.selectbox(
        "View Mode",
        options=["Tail (last 100)", "Tail (last 500)", "Tail (last 1000)", "Full File"]
    )

# Parse view mode
if view_mode.startswith("Tail"):
    # Extract number from "Tail (last N)"
    match = re.search(r'\(last (\d+)\)', view_mode)
    if match:
        max_lines = int(match.group(1))
        from_end = True
    else:
        max_lines = 100
        from_end = True
else:
    max_lines = None
    from_end = False

st.divider()

# Read and filter logs
log_lines = read_log_file(selected_file, max_lines=max_lines, from_end=from_end)

# Apply filters
filtered_lines = filter_logs(log_lines, log_level if log_level != "ALL" else None, keyword if keyword else None)

# Display stats
col_stats1, col_stats2, col_stats3 = st.columns(3)
with col_stats1:
    st.metric("Total Lines", len(log_lines))
with col_stats2:
    st.metric("Filtered Lines", len(filtered_lines))
with col_stats3:
    if log_lines:
        filter_percentage = (len(filtered_lines) / len(log_lines)) * 100
        st.metric("Match Rate", f"{filter_percentage:.1f}%")

st.divider()

# Display logs
st.subheader("📄 Log Content")

if filtered_lines:
    # Create log display
    log_content = "".join(filtered_lines)

    # Option to show with highlighting
    col_display1, col_display2 = st.columns([3, 1])
    with col_display1:
        st.markdown("**Display Options:**")
    with col_display2:
        show_highlighting = st.checkbox("Syntax Highlighting", value=True)

    if show_highlighting:
        # Display with HTML highlighting
        highlighted_content = ""
        for line in filtered_lines:
            highlighted_line = highlight_log_level(line)
            highlighted_content += highlighted_line

        st.markdown(
            f'<div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; '
            f'font-family: monospace; font-size: 12px; height: 600px; overflow-y: scroll; white-space: pre-wrap;">'
            f'{highlighted_content}</div>',
            unsafe_allow_html=True
        )
    else:
        # Display as plain text
        st.text_area(
            "Log Content",
            value=log_content,
            height=600,
            label_visibility="collapsed"
        )

    # Action buttons
    st.divider()
    col_action1, col_action2, col_action3, col_action4 = st.columns(4)

    with col_action1:
        # Download button
        st.download_button(
            label="📥 Download Filtered Logs",
            data=log_content,
            file_name=f"{selected_file.stem}_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            mime="text/plain",
            width='stretch'
        )

    with col_action2:
        # Download original file
        with open(selected_file, 'r', encoding='utf-8', errors='replace') as f:
            original_content = f.read()
        st.download_button(
            label="📥 Download Original",
            data=original_content,
            file_name=selected_file.name,
            mime="text/plain",
            width='stretch'
        )

    with col_action3:
        # Clear filters
        if st.button("🔄 Clear Filters", width='stretch'):
            st.rerun()

    with col_action4:
        # Refresh
        if st.button("🔄 Refresh", width='stretch'):
            st.cache_data.clear()
            st.rerun()

else:
    st.warning("⚠️ No log lines match the current filters")
    if st.button("Clear Filters"):
        st.rerun()

st.divider()

# Tips
st.info("""
💡 **Tips:**
- Use **Tail mode** for large log files to view only recent entries
- **Auto-refresh** to monitor logs in real-time
- **Syntax Highlighting** makes it easier to spot errors and warnings
- Use **keyword search** to find specific events or errors
- **Download** filtered logs for detailed analysis
""")
