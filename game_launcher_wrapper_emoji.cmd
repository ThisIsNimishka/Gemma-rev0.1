@echo off
REM Wrapper to launch SDR Game Launcher Wrapper
REM Redirects to game_launcher_wrapper.cmd

if "%~1"=="" (
    echo Error: No process name provided
    echo Usage: game_launcher_wrapper_emoji.cmd "processname.exe"
    pause
    exit /b 1
)

REM Call the main wrapper script
call "%~dp0game_launcher_wrapper.cmd" "%~1"

exit /b %ERRORLEVEL%
