@echo off
chcp 65001 >nul
title Go bo Proxy Server Service
echo ========================================
echo      Go bo Python Proxy Server Service
echo ========================================
echo.

:: Kiểm tra quyền admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Dang chay voi quyen Administrator
) else (
    echo [ERROR] Can quyen Administrator de go bo service!
    echo Vui long chay file nay voi quyen Administrator.
    pause
    exit /b 1
)

:: Kiểm tra NSSM đã được cài đặt chưa
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] NSSM chua duoc cai dat!
    echo Khong the go bo service ma khong co NSSM.
    pause
    exit /b 1
)

echo.
echo Dang kiem tra service...
sc query "ProxyServer" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Service "ProxyServer" khong ton tai hoac da duoc go bo.
    echo.
    pause
    exit /b 0
)

echo [OK] Tim thay service "ProxyServer"
echo.

:: Hiển thị trạng thái hiện tại
echo Trang thai hien tai:
sc query "ProxyServer" | findstr "STATE"
echo.

echo Dang dung service...
nssm stop ProxyServer

:: Đợi service dừng hoàn toàn
timeout /t 3 /nobreak >nul

echo Dang go bo service...
nssm remove ProxyServer confirm

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo   Service da duoc go bo thanh cong!
    echo ========================================
    echo.
    echo Service "ProxyServer" da duoc go bo khoi Windows Services.
    echo.
    echo Luu y:
    echo - Log files van duoc giu lai trong thu muc hien tai
    echo - NSSM van duoc cai dat tren he thong
    echo - Ban co the cai dat lai service bang "install_service.bat"
    echo.
) else (
    echo.
    echo [ERROR] Co loi xay ra khi go bo service!
    echo Vui long thu go bo thu cong bang Windows Services Manager.
    echo.
)

pause