================================================================
  SUT Service Installer Package
  Automated Game Testing Service for System Under Test (SUT)
================================================================

CONTENTS:
---------
1. gemma_sut_service_improved_3.1.py - Source code
2. build_sut_service.bat             - Build EXE from source
3. install_sut_service.bat           - Install as auto-start service
4. uninstall_sut_service.bat         - Remove service completely
5. start_sut_service.bat             - Manual start service
6. stop_sut_service.bat              - Manual stop service

INSTALLATION STEPS:
-------------------

1. BUILD THE EXECUTABLE:
   - Double-click: build_sut_service.bat
   - Wait for PyInstaller to create SUTService.exe
   - Output will be in: dist\SUTService.exe

2. INSTALL AS AUTO-START SERVICE:
   - Right-click: install_sut_service.bat
   - Select: "Run as Administrator"
   - Service will be installed to: C:\Program Files\SUTService\
   - Auto-start scheduled task will be created

3. SERVICE WILL NOW:
   - Start automatically at system boot
   - Run with Administrator privileges
   - Show console window with live logs
   - Listen on port 8080 (default)

USAGE:
------

START SERVICE:
  - Automatic: Reboot computer, service starts automatically
  - Manual: Double-click start_sut_service.bat

STOP SERVICE:
  - Double-click: stop_sut_service.bat
  - Or: Close the console window

UNINSTALL:
  - Right-click: uninstall_sut_service.bat
  - Select: "Run as Administrator"

CHECK IF RUNNING:
  - Look for SUTService console window
  - Or test: http://localhost:8080/health

REQUIREMENTS:
-------------
- Python 3.x (for building)
- PyInstaller (auto-installed by build script)
- Windows 10/11
- Administrator privileges (for installation)

SERVICE DETAILS:
----------------
- Port: 8080 (HTTP REST API)
- Admin: YES (required for game input)
- Auto-start: YES (via scheduled task)
- Console: Visible (shows live logs)
- Installation: C:\Program Files\SUTService\

API ENDPOINTS:
--------------
- GET  /health      - Health check
- GET  /status      - Service status
- GET  /screenshot  - Capture screenshot
- POST /launch      - Launch game
- POST /action      - Perform keyboard/mouse action
  Actions: click, key, text, scroll, hotkey, double_click, drag, wait

SUPPORTED ACTIONS:
------------------
- Mouse clicks (left/right/middle)
- Double-click
- Drag and drop
- Smooth mouse movement
- Keyboard input
- Hotkeys (Ctrl+S, Alt+Tab, etc.)
- Text input
- Mouse scrolling
- Game process management

TROUBLESHOOTING:
----------------

Q: Build fails?
A: Install Python dependencies:
   pip install flask pyautogui psutil pywin32

Q: Service won't start?
A: Check Windows Firewall, port 8080 must be open

Q: Input not working in games?
A: Ensure service is running as Administrator

Q: Service not auto-starting?
A: Check Task Scheduler for "SUTService" task

Q: Multiple instances running?
A: Run stop_sut_service.bat first, then start again

NOTES:
------
- Service must run as Administrator for game input
- Console window shows real-time logs
- Minimizing console window is OK, service keeps running
- Closing console window stops the service
- Port 8080 must not be used by other applications

================================================================
For support, check the source code or logs:
C:\Program Files\SUTService\improved_sut_service.log
================================================================
