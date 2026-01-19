@echo off
REM Game Launcher Wrapper with SDR Support
REM This script launches SDRTrayApp.exe before the game and stops it after.

if "%~1"=="" (
    echo Error: No process name provided
    echo Usage: game_launcher_wrapper.cmd "processname.exe"
    pause
    exit /b 1
)

set "PROCESS_NAME=%~1"
set "SDR_PATH=C:\Program Files\Intel Corporation\Intel(R)SystemDataRecorder\SDRTrayApp.exe"

echo ------------------------------------------------
echo Starting SDR Tray App...
echo Path: "%SDR_PATH%"
if exist "%SDR_PATH%" (
    start "" "%SDR_PATH%"
) else (
    echo WARNING: SDRTrayApp.exe not found at specified path.
    echo Proceeding with game launch anyway...
)
echo ------------------------------------------------

echo Waiting for process "%PROCESS_NAME%" to start...

:wait_for_start
tasklist /FI "IMAGENAME eq %PROCESS_NAME%" 2>NUL | find /I /N "%PROCESS_NAME%">NUL
if "%ERRORLEVEL%"=="0" goto process_started
timeout /t 1 /nobreak >NUL
goto wait_for_start

:process_started
echo Process "%PROCESS_NAME%" detected. Monitoring...
echo.

:monitor_process
tasklist /FI "IMAGENAME eq %PROCESS_NAME%" 2>NUL | find /I /N "%PROCESS_NAME%">NUL
if "%ERRORLEVEL%"=="1" goto process_stopped
timeout /t 2 /nobreak >NUL
goto monitor_process

:process_stopped
echo Process "%PROCESS_NAME%" has stopped.
echo.
echo ------------------------------------------------
echo Stopping SDR Tray App...
taskkill /IM "SDRTrayApp.exe" /F 2>NUL
if "%ERRORLEVEL%"=="0" (
    echo SDR Tray App stopped successfully.
) else (
    echo SDR Tray App was not running or could not be stopped.
)
echo ------------------------------------------------

exit /b 0
