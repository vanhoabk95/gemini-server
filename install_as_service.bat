@echo off
echo This script will install the Python Proxy Server as a Windows service
echo.
echo NOTE: This script requires NSSM (Non-Sucking Service Manager) to be installed
echo and available in your PATH. If NSSM is not installed, the script will
echo provide instructions for downloading and installing it.
echo.
echo Press any key to continue...
pause > nul

:: Check if NSSM exists
where nssm > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: NSSM (Non-Sucking Service Manager) not found.
    echo Please download NSSM from https://nssm.cc/download
    echo Extract the nssm.exe file for your system architecture to a directory in your PATH.
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

:: Get the full path to the main.py script
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%main.py"

:: Install the service
echo Installing Python Proxy Server as a service...
nssm install "Python Proxy Server" "python" "%SCRIPT_PATH% --host 0.0.0.0 --port 80 --max-connections 50 --log-level DEBUG"
nssm set "Python Proxy Server" Description "Python HTTP Proxy Server"
nssm set "Python Proxy Server" DisplayName "Python Proxy Server"
nssm set "Python Proxy Server" Start SERVICE_AUTO_START
nssm set "Python Proxy Server" AppStdout "%SCRIPT_DIR%proxy_service.log"
nssm set "Python Proxy Server" AppStderr "%SCRIPT_DIR%proxy_service_error.log"

echo.
echo Service installed successfully!
echo You can start, stop and configure the service using Windows Services console (services.msc)
echo or with the following commands:
echo.
echo   net start "Python Proxy Server"
echo   net stop "Python Proxy Server"
echo   sc delete "Python Proxy Server"    (to uninstall)
echo.
pause 