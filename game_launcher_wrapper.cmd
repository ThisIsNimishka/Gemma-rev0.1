@echo off
REM Game Launcher Wrapper with SDR Support
REM This script launches SDRTrayAppCmdLine.exe before the game and stops it after.

if "%~1"=="" (
    echo Error: No process name provided
    echo Usage: game_launcher_wrapper.cmd "processname.exe" [testcase_id] [user_name] [log_collectors] [test_domain] [test_name]
    pause
    exit /b 1
)

set "PROCESS_NAME=%~1"
set "TCID=%~2"
set "USER_NAME=%~3"
set "COLLECTORS=%~4"
set "TDOMAIN=%~5"
set "TNAME=%~6"

if "%TCID%"=="" set "TCID=PSPV-TC-10391"
if "%USER_NAME%"=="" set "USER_NAME=%USERNAME%"
if "%COLLECTORS%"=="" set "COLLECTORS=WLAN,PnP,ETL"

set "SDR_PATH=C:\OWR\SDR\Intel(R)SystemDataRecorder_OneBKC\SDRBinaries\SDRApplication\SDRTrayAppCmdLine\SDRTrayAppCmdLine.exe"

echo ------------------------------------------------
echo 1) Enable log collection (pre-req)
if exist "%SDR_PATH%" (
    "%SDR_PATH%" --log-collection --enable=Yes
)

echo 2) Starting SDR Monitoring...
set START_CMD="%SDR_PATH%" --start --testcase-id=%TCID% --user-name=%USER_NAME% --team-name=SIV --run-type=Debug --log-collectors=%COLLECTORS%

if not "%TDOMAIN%"=="" (
    set START_CMD=%START_CMD% --test-domain="%TDOMAIN%"
)
if not "%TNAME%"=="" (
    set START_CMD=%START_CMD% --test-name="%TNAME%"
)

echo Command: %START_CMD%

if exist "%SDR_PATH%" (
    %START_CMD%
) else (
    echo WARNING: SDRTrayAppCmdLine.exe not found at %SDR_PATH%
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
if exist "%SDR_PATH%" (
    "%SDR_PATH%" --test-step="Process Started: %PROCESS_NAME%"
)
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
    "%SDR_PATH%" --test-step="Process Stopped: %PROCESS_NAME%"
    "%SDR_PATH%" --stop
) else (
    echo SDRTrayAppCmdLine.exe was not found to stop the process.
)
echo ------------------------------------------------

exit /b 0
