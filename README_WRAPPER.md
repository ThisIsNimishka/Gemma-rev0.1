# Game Process Monitor - Usage Guide

## Overview
The `game_launcher_wrapper.cmd` script monitors a game process and manages the SDR (System Data Recorder) monitoring session.

## How It Works

1. **Starts** the SDR monitoring session using `SDRTrayAppCmdLine.exe --start`.
2. **Waits** for the specified game process to start.
3. **Monitors** the process continuously (checks every 2 seconds).
4. **Stops** the SDR monitoring session using `SDRTrayAppCmdLine.exe --stop` when the game ends.
5. **Exits** automatically.

## Usage

### Basic Usage
```cmd
game_launcher_wrapper.cmd "processname.exe"
```

### Examples

**For a game:**
```cmd
game_launcher_wrapper.cmd "game.exe"
```

## Integration Methods

### Method 1: Run Alongside Game Launch
Start the monitor script in a separate window before or right after launching the game:

```cmd
start game_launcher_wrapper.cmd "game.exe"
start game.exe
```

### Method 2: Python Integration
You can integrate this into your Python code:

```python
import subprocess

# Start the monitor in the background
monitor_process = subprocess.Popen(
    ['game_launcher_wrapper.cmd', 'game.exe'],
    cwd=r'C:\Users\nimishka\Downloads\1. PROJECTS\ISV AUTOMATION WITH VCAP\GEMMA NIGHTELY RELEASE\Gemma-rev0.1'
)

# Launch the game
game_process = subprocess.Popen(['game.exe'])

# Wait for monitor to complete (it will exit when game closes)
monitor_process.wait()
```

## Example Output

```
[Starting SDR Monitoring...]
Command: "C:\Program Files\Intel Corporation\Intel(R)SystemDataRecorder\SDRTrayAppCmdLine.exe" --start
[Waiting for process to start...]
Process "game.exe" detected. Monitoring active.
[Monitoring process...]
[Process terminates]
Process "game.exe" has stopped.
Stopping SDR Monitoring...
```

## Notes

- The script checks for the process every 2 seconds while monitoring.
- The script automatically handles starting and stopping the SDR session.
- Process name must include the `.exe` extension.
- The script automatically exits when the monitored process terminates.
