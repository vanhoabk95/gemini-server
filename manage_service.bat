@echo off
chcp 65001 >nul
title Quan ly Proxy Server Service
echo ========================================
echo      Quan ly Python Proxy Server Service
echo ========================================
echo.

:: Kiểm tra NSSM đã được cài đặt chưa
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] NSSM chua duoc cai dat!
    echo Vui long chay "install_nssm.bat" truoc.
    pause
    exit /b 1
)

:MENU
cls
echo ========================================
echo      Quan ly Python Proxy Server Service
echo ========================================
echo.

:: Kiểm tra service có tồn tại không
sc query "ProxyServer" >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Service "ProxyServer" chua duoc cai dat!
    echo.
    echo 1. Cai dat Service
echo 2. Thoat
    echo.
    set /p choice="Chon tuy chon (1-2): "
    
    if "%choice%"=="1" (
        echo.
        echo Dang chay install_service.bat...
        call install_service.bat
        goto MENU
    )
    if "%choice%"=="2" exit /b 0
    goto MENU
)

:: Lấy trạng thái service
for /f "tokens=4" %%i in ('sc query "ProxyServer" ^| findstr "STATE"') do set "SERVICE_STATE=%%i"

echo Trang thai hien tai: %SERVICE_STATE%
echo.
echo 1. Khoi dong Service
echo 2. Dung Service  
echo 3. Khoi dong lai Service
echo 4. Xem trang thai chi tiet
echo 5. Xem log files
echo 6. Mo Windows Services Manager
echo 7. Go bo Service
echo 8. Thoat
echo.
set /p choice="Chon tuy chon (1-8): "

if "%choice%"=="1" goto START_SERVICE
if "%choice%"=="2" goto STOP_SERVICE
if "%choice%"=="3" goto RESTART_SERVICE
if "%choice%"=="4" goto STATUS_SERVICE
if "%choice%"=="5" goto VIEW_LOGS
if "%choice%"=="6" goto OPEN_SERVICES
if "%choice%"=="7" goto UNINSTALL_SERVICE
if "%choice%"=="8" exit /b 0
goto MENU

:START_SERVICE
echo.
echo Dang khoi dong service...
nssm start ProxyServer
if %errorLevel% == 0 (
    echo [OK] Service da duoc khoi dong thanh cong!
) else (
    echo [ERROR] Khong the khoi dong service!
)
echo.
pause
goto MENU

:STOP_SERVICE
echo.
echo Dang dung service...
nssm stop ProxyServer
if %errorLevel% == 0 (
    echo [OK] Service da duoc dung thanh cong!
) else (
    echo [ERROR] Khong the dung service!
)
echo.
pause
goto MENU

:RESTART_SERVICE
echo.
echo Dang khoi dong lai service...
nssm restart ProxyServer
if %errorLevel% == 0 (
    echo [OK] Service da duoc khoi dong lai thanh cong!
) else (
    echo [ERROR] Khong the khoi dong lai service!
)
echo.
pause
goto MENU

:STATUS_SERVICE
echo.
echo ========================================
echo           Trang thai Service
echo ========================================
sc query "ProxyServer"
echo.
echo ========================================
echo          Cau hinh Service
echo ========================================
sc qc "ProxyServer"
echo.
pause
goto MENU

:VIEW_LOGS
echo.
echo ========================================
echo              Log Files
echo ========================================
echo.
if exist "service_output.log" (
    echo [Output Log - 20 dòng cuối:]
    echo ----------------------------------------
    powershell -Command "& {Get-Content 'service_output.log' -Tail 20}"
    echo.
) else (
    echo [INFO] Khong tim thay service_output.log
)

if exist "service_error.log" (
    echo [Error Log - 20 dòng cuối:]
    echo ----------------------------------------
    powershell -Command "& {Get-Content 'service_error.log' -Tail 20}"
    echo.
) else (
    echo [INFO] Khong tim thay service_error.log
)
pause
goto MENU

:OPEN_SERVICES
echo.
echo Dang mo Windows Services Manager...
services.msc
goto MENU

:UNINSTALL_SERVICE
echo.
echo Ban co chac chan muon go bo service khong? (Y/N)
set /p confirm="Nhap Y de xac nhan: "
if /i "%confirm%"=="Y" (
    echo.
    echo Dang chay uninstall_service.bat...
    call uninstall_service.bat
)
goto MENU