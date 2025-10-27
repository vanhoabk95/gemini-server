"""
Statistics Page - Request Statistics Dashboard

Displays detailed statistics about proxy requests with interactive charts.
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Statistics - Proxy Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Request Statistics")
st.markdown("Detailed analysis of proxy server requests")

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

def calculate_metrics(stats_data):
    """Calculate aggregate metrics from stats data."""
    if not stats_data or not stats_data.get('stats'):
        return None

    all_stats = stats_data['stats']

    metrics = {
        'total_ips': len(all_stats),
        'total_requests': sum(s.get('total_requests', 0) for s in all_stats.values()),
        'http_requests': sum(s.get('http_requests', 0) for s in all_stats.values()),
        'https_requests': sum(s.get('https_requests', 0) for s in all_stats.values()),
        'gemini_requests': sum(s.get('gemini_requests', 0) for s in all_stats.values()),
        'success_count': sum(s.get('success_count', 0) for s in all_stats.values()),
        'failed_count': sum(s.get('failed_count', 0) for s in all_stats.values()),
    }

    total = metrics['success_count'] + metrics['failed_count']
    metrics['success_rate'] = (metrics['success_count'] / total * 100) if total > 0 else 0

    return metrics

# Load data
stats_data = load_stats()

if not stats_data:
    st.warning("⚠️ No statistics data available. Make sure the proxy server is running and has processed some requests.")
    st.stop()

# Calculate metrics
metrics = calculate_metrics(stats_data)

if not metrics:
    st.error("Unable to calculate metrics from stats data")
    st.stop()

# Display summary metrics
st.subheader("Summary Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total IPs", f"{metrics['total_ips']:,}")
with col2:
    st.metric("Total Requests", f"{metrics['total_requests']:,}")
with col3:
    st.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
with col4:
    total_failed = metrics['failed_count']
    st.metric("Failed Requests", f"{total_failed:,}")

st.divider()

# Charts section
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Request Types Distribution")

    # Pie chart for request types
    request_types_data = {
        'Type': ['HTTP', 'HTTPS', 'Gemini'],
        'Count': [
            metrics['http_requests'],
            metrics['https_requests'],
            metrics['gemini_requests']
        ]
    }
    df_types = pd.DataFrame(request_types_data)
    df_types = df_types[df_types['Count'] > 0]  # Filter out zero values

    if not df_types.empty:
        fig_pie = px.pie(
            df_types,
            values='Count',
            names='Type',
            color='Type',
            color_discrete_map={'HTTP': '#636EFA', 'HTTPS': '#EF553B', 'Gemini': '#00CC96'},
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie)
    else:
        st.info("No request data available")

with col_chart2:
    st.subheader("Success vs Failed Requests")

    # Donut chart for success/failure
    success_data = {
        'Status': ['Success', 'Failed'],
        'Count': [metrics['success_count'], metrics['failed_count']]
    }
    df_success = pd.DataFrame(success_data)

    fig_success = px.pie(
        df_success,
        values='Count',
        names='Status',
        color='Status',
        color_discrete_map={'Success': '#00CC96', 'Failed': '#EF553B'},
        hole=0.4
    )
    fig_success.update_traces(textposition='inside', textinfo='percent+label')
    fig_success.update_layout(height=400)
    st.plotly_chart(fig_success)

st.divider()

# Top IPs chart
st.subheader("Top 10 IPs by Request Count")

all_stats = stats_data['stats']
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

st.divider()

# Detailed IP Statistics Table
st.subheader("Detailed IP Statistics")

# Create DataFrame
ip_list = []
for ip, stats in all_stats.items():
    ip_list.append({
        'IP Address': ip,
        'Total Requests': stats.get('total_requests', 0),
        'HTTP': stats.get('http_requests', 0),
        'HTTPS': stats.get('https_requests', 0),
        'Gemini': stats.get('gemini_requests', 0),
        'Success': stats.get('success_count', 0),
        'Failed': stats.get('failed_count', 0),
        'Success Rate': f"{(stats.get('success_count', 0) / stats.get('total_requests', 1) * 100):.1f}%",
        'First Seen': stats.get('first_seen', 'N/A'),
        'Last Seen': stats.get('last_seen', 'N/A')
    })

df_ips = pd.DataFrame(ip_list)

# Sort options
col_sort1, col_sort2 = st.columns([1, 3])
with col_sort1:
    sort_by = st.selectbox(
        "Sort by",
        options=['Total Requests', 'HTTP', 'HTTPS', 'Gemini', 'Success', 'Failed', 'IP Address'],
        index=0
    )
with col_sort2:
    sort_order = st.radio("Order", options=['Descending', 'Ascending'], horizontal=True)

# Sort DataFrame
df_ips_sorted = df_ips.sort_values(
    by=sort_by,
    ascending=(sort_order == 'Ascending')
)

# Display table
st.dataframe(
    df_ips_sorted,
    width='stretch',
    hide_index=True,
    height=400
)

# Export options
st.divider()
col_export1, col_export2, col_export3 = st.columns([1, 1, 2])

with col_export1:
    # Convert to CSV
    csv = df_ips_sorted.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"proxy_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        width='stretch'
    )

with col_export2:
    if st.button("🔄 Refresh Data", width='stretch'):
        st.cache_data.clear()
        st.rerun()

with col_export3:
    # Display last update time
    generated_at = stats_data.get('generated_at', 'Unknown')
    if generated_at != 'Unknown':
        try:
            dt = datetime.fromisoformat(generated_at)
            generated_at = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    st.info(f"📅 Last updated: {generated_at}")
