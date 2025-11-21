@echo off
echo ================================================================
echo  Stopping SUT Service
echo ================================================================
echo.

REM Check if running
tasklist /FI "IMAGENAME eq SUTService.exe" 2>nul | find /I "SUTService.exe" >nul
if errorlevel 1 (
    echo SUT Service is not running
    echo.
    pause
    exit /b 0
)

REM Stop the service
echo Stopping SUT Service...
taskkill /F /IM SUTService.exe

timeout /t 2 /nobreak >nul

REM Verify stopped
tasklist /FI "IMAGENAME eq SUTService.exe" 2>nul | find /I "SUTService.exe" >nul
if errorlevel 1 (
    echo.
    echo ================================================================
    echo SUT Service stopped successfully!
    echo ================================================================
) else (
    echo ERROR: Failed to stop service
)

echo.
pause
