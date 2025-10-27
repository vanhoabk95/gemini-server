@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
streamlit run dashboard.py --server.headless true --server.port 8501
