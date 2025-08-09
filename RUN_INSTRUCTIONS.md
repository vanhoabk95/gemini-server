# Python Proxy Server - Windows Run Options

This directory contains several batch files to help you run the Python Proxy Server on Windows with different configurations.

## Available Options

1. **start_proxy.bat**
   - Basic option to run the proxy server
   - Settings: host=0.0.0.0, port=80, max-connections=50
   - Usage: Double-click the file

2. **start_proxy_admin.bat**
   - Runs the proxy server with administrator privileges
   - Required for using port 80 on Windows
   - Automatically requests elevation if needed
   - Usage: Double-click the file (UAC prompt will appear)

3. **start_proxy_minimized.bat**
   - Runs the proxy server in a minimized window
   - The server window appears in the taskbar but doesn't take focus
   - Usage: Double-click the file

4. **install_as_service.bat**
   - Installs the proxy server as a Windows service (runs at system startup)
   - Requires NSSM (Non-Sucking Service Manager) to be installed
   - Usage: Run as administrator

## Command Line Options

If you prefer to run the proxy server from the command line, use:

```
python main.py --host 0.0.0.0 --port 80 --max-connections 50
```

You can customize any of these settings as needed.

## Stopping the Server

- For batch files: Press Ctrl+C in the command window
- For Windows service: Use `services.msc` or run `net stop "Python Proxy Server"` 