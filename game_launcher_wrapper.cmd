@echo off
REM Game Launcher Wrapper with SDR Support
REM This script launches SDRTrayAppCmdLine.exe before the game and stops it after.

if "%~1"=="" (
    echo Error: No process name provided
    echo Usage: game_launcher_wrapper.cmd "processname.exe"
    pause
    exit /b 1
)

set "PROCESS_NAME=%~1"
set "SDR_PATH=C:\Program Files\Intel Corporation\Intel(R)SystemDataRecorder\SDRTrayAppCmdLine.exe"

echo ------------------------------------------------
echo Starting SDR Monitoring...
echo Command: "%SDR_PATH%" --start
if exist "%SDR_PATH%" (
    "%SDR_PATH%" --start
) else (
    echo WARNING: SDRTrayAppCmdLine.exe not found at specified path.
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
echo Process "%PROCESS_NAME%" detected. Monitoring active.
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
echo Stopping SDR Monitoring...
if exist "%SDR_PATH%" (
    "%SDR_PATH%" --stop
) else (
    echo SDRTrayAppCmdLine.exe was not found to stop the process.
)
echo ------------------------------------------------

exit /b 0
