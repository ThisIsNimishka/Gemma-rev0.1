# Emoji Support for SDR Monitor

## Overview
I've created **three versions** of the SDR Monitor with different levels of emoji support:

## Files Created

### 1. **game_launcher_wrapper.cmd** (Original - Basic Emoji Support)
- Standard CMD file with UTF-8 encoding enabled
- Emojis may display as boxes or question marks depending on your console font
- Works on all Windows systems without PowerShell

**Usage:**
```cmd
game_launcher_wrapper.cmd "mspaint.exe"
```

### 2. **game_launcher_wrapper.ps1** (PowerShell - Full Emoji Support ✅ RECOMMENDED)
- Full emoji support with colors
- Beautiful colored output (Green, Red, Yellow, Cyan, etc.)
- Requires PowerShell (built into Windows 10/11)

**Usage:**
```powershell
powershell.exe -ExecutionPolicy Bypass -File game_launcher_wrapper.ps1 -ProcessName "mspaint.exe"
```

### 3. **game_launcher_wrapper_emoji.cmd** (Easy Launcher for PowerShell)
- CMD wrapper that automatically launches the PowerShell version
- Best of both worlds: Easy to use + Full emoji support
- Just double-click or run from command line

**Usage:**
```cmd
game_launcher_wrapper_emoji.cmd "mspaint.exe"
```

## Which One Should You Use?

### 🏆 **RECOMMENDED: game_launcher_wrapper_emoji.cmd**
This is the easiest to use and has full emoji support!

```cmd
game_launcher_wrapper_emoji.cmd "mspaint.exe"
```

## Testing

### Quick Test:
```cmd
start mspaint
game_launcher_wrapper_emoji.cmd "mspaint.exe"
```

Then close MS Paint to see the full output!

## Example Output (PowerShell Version)

**When Process Starts:**
```
========================================
   🎮 BANDARUR HAS BEEN SUMMONED! 🎮
========================================

  ⚔️  SDR is FORCED to start! ⚔️

  Status: ALIVE AND KICKING!
  Mission: Monitor mspaint.exe
  Mood: Reluctantly Obedient 😤

========================================
```

**When Process Stops:**
```
========================================
   💀 BANDARUR HAS BEEN TERMINATED! 💀
========================================

  ⚰️  SDR is FORCED to kill! ⚰️

  Status: DEAD (Finally free!)
  Last Words: "I'll be back... maybe"
  Cause of Death: Process Termination

========================================
  Thanks for using SDR Monitor™
  (He didn't enjoy it)
========================================
```

## Troubleshooting

### If emojis don't display in CMD:
1. Use the PowerShell version instead (`game_launcher_wrapper_emoji.cmd`)
2. Or change your console font to "Cascadia Code" or "Consolas"
3. Right-click CMD title bar → Properties → Font → Select a Unicode font

### If PowerShell execution is blocked:
Run this command once as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or use the `game_launcher_wrapper_emoji.cmd` which bypasses this automatically!
