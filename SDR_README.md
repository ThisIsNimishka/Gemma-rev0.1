# SDR Integration & Usage Guide

This document provides comprehensive information about the System Data Recorder (SDR) integration, specifically dealing with the `game_launcher_wrapper.cmd` script which automates the monitoring process.

## Wrapper Utility: `game_launcher_wrapper.cmd`

The `game_launcher_wrapper.cmd` script is designed to automatically manage the SDR lifecycle around a specific game or application process. It handles starting the SDR service, checking for process existence, and stopping the service when the process terminates.

### Command Syntax

```cmd
game_launcher_wrapper.cmd "ProcessName.exe" [TestCaseID] [UserName] [LogCollectors] [TestDomain] [TestName]
```

### Parameters

| Parameter | Required | Default Value | Description |
|-----------|:--------:|---------------|-------------|
| **ProcessName.exe** | Yes | N/A | The executable name of the game/app to monitor. **Must include .exe**. |
| **TestCaseID** | No | `PSPV-TC-10391` | The specific test case ID for the SDR session. |
| **UserName** | No | `%USERNAME%` | The user name to log associated with the session. |
| **LogCollectors** | No | `WLAN,PnP,ETL` | Comma-separated list of log collectors to enable. |
| **TestDomain** | No | *Empty* | The domain category for the test (e.g., thermal_management). |
| **TestName** | No | *Empty* | A friendly name for the specific test run. |

### Workflow Description

1. **Pre-check**: The script sets up the environment and defaults.
2. **Enable Logging**: Runs `--log-collection --enable=Yes`.
3. **Start SDR**: Launches `SDRTrayAppCmdLine.exe --start` with the provided parameters.
   - Sets run-type to `Debug`.
   - Sets team-name to `SIV`.
4. **Wait for Process**: Loops indefinitely (checking every 1 second) until `ProcessName.exe` appears in the task list.
   - *Note: You must launch the game separately, commonly via a separate `start` command or Python subprocess.*
5. **Monitor Loop**: Once detected, it checks every 2 seconds to ensure the process is still running.
   - Logs a `--test-step="Process Started: ..."` event to SDR.
6. **Stop SDR**: When the process disappears from the task list:
   - Logs a `--test-step="Process Stopped: ..."` event.
   - Executes `--stop` to finalize the SDR session.

## Integration Examples

### 1. Manual / Batch File Usage

To run a game manually with SDR wrapper:

```cmd
@echo off
REM Start the wrapper in the background (or separate window)
start "" cmd /c game_launcher_wrapper.cmd "my_game.exe" "TC-999" "Tester1"

REM Launch the game immediately after
start "" "C:\Games\my_game.exe"
```

### 2. Python Usage

Integrating into a Python automation script:

```python
import subprocess
import time

wrapper_script = "game_launcher_wrapper.cmd"
game_exe = "Cyberpunk2077.exe"
sdr_args = [wrapper_script, game_exe, "TC-PERF-001", "AutoUser", "CPU,GPU,Power"]

# 1. Start the wrapper (non-blocking)
wrapper_process = subprocess.Popen(sdr_args, creationflags=subprocess.CREATE_NEW_CONSOLE)

# Give it a moment to initialize
time.sleep(2)

# 2. Start the game
game_process = subprocess.Popen([r"C:\Path\To\Cyberpunk2077.exe"])

# 3. Wait for the wrapper to finish (which happens when game closes)
wrapper_process.wait()
print("SDR Session Completed.")
```

## Underlying SDR Configuration

The wrapper script points to the following default SDR path:
`C:\OWR\SDR\Intel(R)SystemDataRecorder_OneBKC\SDRBinaries\SDRApplication\SDRTrayAppCmdLine\SDRTrayAppCmdLine.exe`

If this path does not exist, the wrapper will print a warning but allow the game launch flow to proceed (without SDR data collection).
