@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

REM Start Proxy Server in background
start /b python main.py

REM Wait for proxy to start
timeout /t 3 /nobreak >nul

REM Start Dashboard headless (blocks until stopped)
streamlit run dashboard.py --server.headless true --server.port 8501
