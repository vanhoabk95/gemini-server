@echo off
title Proxy Server (Port 80)
echo ========================================
echo    Simple Python Proxy Server
echo ========================================
echo.
echo Starting server...
echo Host: 0.0.0.0
echo Port: 80 (requires admin privileges)
echo Max Connections: 150
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python main.py

pause