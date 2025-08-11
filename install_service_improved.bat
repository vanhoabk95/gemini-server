@echo off
chcp 65001 >nul
title Cai dat Service - Phien ban cai tien
echo ========================================
echo   Cai dat Service - Phien ban cai tien
echo ========================================
echo.

:: Kiểm tra quyền admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Dang chay voi quyen Administrator
) else (
    echo [ERROR] Can quyen Administrator de cai dat service!
    echo Vui long chay file nay voi quyen Administrator.
    pause
    exit /b 1
)

:: Kiểm tra NSSM
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] NSSM chua duoc cai dat!
    echo Vui long chay "install_nssm.bat" truoc.
    pause
    exit /b 1
)

echo.
echo Dang kiem tra service hien tai...
sc query "ProxyServer" >nul 2>&1
if %errorLevel% == 0 (
    echo [WARNING] Service "ProxyServer" da ton tai!
    echo Dang go bo service cu...
    nssm stop ProxyServer >nul 2>&1
    nssm remove ProxyServer confirm >nul 2>&1
    echo [OK] Da go bo service cu
    echo.
)

:: Lấy đường dẫn hiện tại
set "CURRENT_DIR=%~dp0"
set "PYTHON_SCRIPT=%CURRENT_DIR%main.py"

:: Kiểm tra file main.py
if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] Khong tim thay file main.py tai: %PYTHON_SCRIPT%
    pause
    exit /b 1
)

echo [OK] Tim thay main.py tai: %PYTHON_SCRIPT%
echo.

:: Tìm Python tốt nhất (không phải từ Microsoft Store)
echo Dang tim Python...
set "BEST_PYTHON="

:: Tìm Python từ registry và các vị trí thông thường
for %%p in (
    "C:\Python312\python.exe"
    "C:\Python311\python.exe" 
    "C:\Python310\python.exe"
    "C:\Python39\python.exe"
    "C:\Python38\python.exe"
) do (
    if exist "%%p" (
        set "BEST_PYTHON=%%p"
        goto FOUND_PYTHON
    )
)

:: Tìm trong Program Files
for /d %%d in ("C:\Program Files\Python*") do (
    if exist "%%d\python.exe" (
        set "BEST_PYTHON=%%d\python.exe"
        goto FOUND_PYTHON
    )
)

:: Nếu không tìm thấy, dùng python từ PATH nhưng cảnh báo
where python >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=*" %%i in ('where python') do (
        set "PYTHON_PATH=%%i"
        goto CHECK_PYTHON_PATH
    )
) else (
    echo [ERROR] Khong tim thay Python! Vui long cai dat Python.
    pause
    exit /b 1
)

:CHECK_PYTHON_PATH
:: Kiểm tra xem có phải từ Microsoft Store không
echo %PYTHON_PATH% | findstr /i "WindowsApps" >nul
if %errorLevel% == 0 (
    echo [WARNING] Python tu Microsoft Store co the khong hoat dong tot voi Service!
    echo De xuat: Cai dat Python tu python.org
    echo.
    echo Ban co muon tiep tuc voi Python hien tai? (Y/N)
    set /p choice="Nhap Y de tiep tuc: "
    if /i not "%choice%"=="Y" (
        echo Huy cai dat. Vui long cai dat Python tu python.org.
        pause
        exit /b 1
    )
    set "BEST_PYTHON=%PYTHON_PATH%"
) else (
    set "BEST_PYTHON=%PYTHON_PATH%"
)
goto FOUND_PYTHON

:FOUND_PYTHON
echo [OK] Su dung Python tai: %BEST_PYTHON%

:: Test Python trước khi cài đặt service
echo.
echo Dang test Python...
"%BEST_PYTHON%" --version
if %errorLevel% neq 0 (
    echo [ERROR] Python khong hoat dong!
    pause
    exit /b 1
)

:: Test chạy script Python
echo.
echo Dang test chay main.py...
echo (Se dung sau 5 giay)
timeout /t 2 /nobreak >nul
start /min "%BEST_PYTHON%" "%PYTHON_SCRIPT%"
timeout /t 5 /nobreak >nul
taskkill /f /im python.exe >nul 2>&1

echo [OK] Python script co the chay duoc
echo.

:: Cài đặt service
echo Dang cai dat service...
nssm install ProxyServer "%BEST_PYTHON%" "%PYTHON_SCRIPT%"

if %errorLevel% neq 0 (
    echo [ERROR] Khong the cai dat service!
    pause
    exit /b 1
)

echo [OK] Service da duoc cai dat
echo.

:: Cấu hình service
echo Dang cau hinh service...
nssm set ProxyServer AppDirectory "%CURRENT_DIR%"
nssm set ProxyServer Description "Python Proxy Server - HTTP/HTTPS Proxy cho LAN"
nssm set ProxyServer Start SERVICE_AUTO_START
nssm set ProxyServer AppExit Default Restart
nssm set ProxyServer AppRestartDelay 5000
nssm set ProxyServer AppStdout "%CURRENT_DIR%service_output.log"
nssm set ProxyServer AppStderr "%CURRENT_DIR%service_error.log"
nssm set ProxyServer AppStdoutCreationDisposition 4
nssm set ProxyServer AppStderrCreationDisposition 4
nssm set ProxyServer AppRotateFiles 1
nssm set ProxyServer AppRotateOnline 1
nssm set ProxyServer AppRotateSeconds 86400
nssm set ProxyServer AppRotateBytes 10485760

echo [OK] Service da duoc cau hinh
echo.

:: Khởi động service
echo Dang khoi dong service...
nssm start ProxyServer

:: Đợi một chút để service khởi động
timeout /t 3 /nobreak >nul

:: Kiểm tra trạng thái service
sc query "ProxyServer" | findstr "RUNNING" >nul
if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo   Service da duoc cai dat thanh cong!
    echo ========================================
    echo.
    echo Ten service: ProxyServer
    echo Trang thai: RUNNING
    echo Khoi dong: Tu dong khi boot Windows
    echo Python path: %BEST_PYTHON%
    echo.
    echo Log files:
    echo - Output: %CURRENT_DIR%service_output.log
    echo - Error:  %CURRENT_DIR%service_error.log
    echo.
    echo Ban co the quan ly service bang:
    echo - services.msc (Windows Services Manager)
    echo - manage_service.bat (script quan ly)
    echo.
) else (
    echo.
    echo [WARNING] Service da duoc cai dat nhung chua chay duoc!
    echo.
    echo Vui long:
    echo 1. Chay "diagnose_service.bat" de chan doan
    echo 2. Kiem tra log files
    echo 3. Chay "fix_python_path.bat" neu can thay doi Python
    echo.
    
    :: Hiển thị log nếu có
    if exist "service_error.log" (
        echo [Error Log - 5 dong cuoi:]
        echo ----------------------------------------
        powershell -Command "& {Get-Content 'service_error.log' -Tail 5}"
        echo.
    )
)

pause