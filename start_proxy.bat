@echo off
echo Starting Python Proxy Server...
echo Host: 0.0.0.0
echo Port: 80
echo Max connections: 50
echo.
echo Press Ctrl+C to stop the server
echo.

uv run python main.py --host 0.0.0.0 --port 80 --max-connections 50 --log-level DEBUG

echo.
echo Server stopped
pause 