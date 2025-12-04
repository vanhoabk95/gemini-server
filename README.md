# Gemini API Gateway

A lightweight proxy server for Google Gemini API with centralized key management, automatic failover, and real-time monitoring.

## Features

- 🔑 **Centralized API Key Management** - Store keys securely on server
- 🔄 **Automatic Failover** - Multiple API keys with auto-switching
- 📊 **Real-time Dashboard** - Monitor usage, stats, and configurations
- 🔥 **Hot Reload** - Update API keys without server restart
- 📈 **Usage Tracking** - 30-day history per API key
- 🚀 **LangChain Compatible** - Works with AI frameworks

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install httpx streamlit pandas plotly

# Or using uv
uv sync
```

### 2. Start Server

```bash
python main.py
```

Server starts on port 80 by default.

### 3. Start Dashboard (Optional)

```bash
streamlit run dashboard.py
```

Access at `http://localhost:8501` to:
- Add/Edit/Delete API configurations
- Monitor usage and statistics
- View logs and errors

### 4. Configure API Keys

**Via Dashboard** (Recommended):
1. Open `http://localhost:8501`
2. Click "Add New Configuration"
3. Enter your Google API key
4. Set model and daily limit

**Via Config File**:
Create/edit `gemini_config.json`:

```json
{
  "configs": [
    {
      "api_key": "YOUR_GOOGLE_API_KEY",
      "model": "gemini-2.0-flash-exp",
      "daily_limit": 1000
    }
  ]
}
```

Get API keys at [Google AI Studio](https://aistudio.google.com/app/apikey)

### 5. Use in Your App

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    api_key="dummy-key",  # Gateway handles real keys
    base_url="http://your-server-ip:80/v1beta"
)

response = llm.invoke("Hello!")
print(response.content)
```

## Configuration Files

**`proxy_config.json`** - Server settings:
```json
{
  "host": "0.0.0.0",
  "port": 80,
  "log_level": "INFO"
}
```

**`gemini_config.json`** - API configurations (managed via dashboard or manually)

## Running as Windows Service

Install as auto-start service:

```bash
# Install service (as admin)
install_service.bat

# Start service
net start ProxyServer
net start ProxyDashboard
```

Manage via `services.msc` or `manage_service.bat`

## Project Structure

```
├── main.py              # Server entry point
├── dashboard.py         # Web dashboard
├── proxy/              # Core modules
│   ├── gemini_handler.py      # API request handler
│   ├── gemini_config.py       # Config management
│   ├── gemini_usage_tracker.py # Usage tracking
│   └── request_stats.py       # Statistics
└── logs/               # Server logs
```

## Troubleshooting

**Server not starting:**
- Check port 80 is available
- Run with admin rights (port 80 requires it)
- Check logs in `logs/proxy_server.log`

**API requests failing:**
- Verify API keys in dashboard
- Check daily limits not exceeded
- Review error messages in dashboard

**Dashboard not loading:**
- Install: `pip install streamlit pandas plotly`
- Start: `streamlit run dashboard.py`

## Security Notes

- ⚠️ Keep `gemini_config.json` private (gitignored)
- ⚠️ Use in trusted networks only
- ✅ API keys never leave the server
- ✅ Clients use dummy credentials

## License

MIT - Educational and development purposes.
