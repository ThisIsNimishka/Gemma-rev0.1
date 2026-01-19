# Game Process Monitor - Usage Guide

## Overview
The `game_launcher_wrapper.cmd` script monitors a game process and prints custom messages when the process starts and stops.

## How It Works

1. **Waits** for the specified process to start
2. **Prints** `SDR is forced to start` when the process is detected
3. **Monitors** the process continuously (checks every 2 seconds)
4. **Prints** `SDR is forced to kill` when the process terminates
5. **Exits** automatically

## Usage

### Basic Usage
```cmd
game_launcher_wrapper.cmd "processname.exe"
```

### Examples

**For MS Paint:**
```cmd
game_launcher_wrapper.cmd "mspaint.exe"
```

**For a game:**
```cmd
game_launcher_wrapper.cmd "game.exe"
```

**For Steam games:**
```cmd
game_launcher_wrapper.cmd "hl2.exe"
```

## Integration Methods

### Method 1: Run Alongside Game Launch
Start the monitor script in a separate window before or right after launching the game:

```cmd
start game_launcher_wrapper.cmd "mspaint.exe"
start mspaint.exe
```

### Method 2: Python Integration
You can integrate this into your Python code to run alongside the game:

```python
import subprocess

# Start the monitor in the background
monitor_process = subprocess.Popen(
    ['game_launcher_wrapper.cmd', 'mspaint.exe'],
    cwd=r'C:\Users\nimishka\Downloads\1. PROJECTS\ISV AUTOMATION WITH VCAP\GEMMA NIGHTELY RELEASE\Gemma-rev0.1'
)

# Launch the game
game_process = subprocess.Popen(['mspaint.exe'])

# Wait for monitor to complete (it will exit when game closes)
monitor_process.wait()
```

### Method 3: Modify SUT Service
Update the `launch_game()` function in `gemma_service_0.2.py` to start the monitor alongside the game.

## Example Output

```
[Waiting for process to start...]
SDR is forced to start
[Monitoring process...]
[Process terminates]
SDR is forced to kill
```

## Notes

- The script checks for the process every 2 seconds while monitoring
- The script waits indefinitely for the process to start (checks every 1 second)
- Process name must include the `.exe` extension
- The script runs in the foreground by default; use `start` command to run in background
- The script automatically exits when the monitored process terminates
