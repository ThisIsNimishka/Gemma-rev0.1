"""
App Launcher module for starting apps on the SUT.
"""

import logging
from typing import Dict, Any

from modules.network import NetworkManager

logger = logging.getLogger(__name__)

class AppLauncher:
    """Handles launching apps on the SUT."""
    
    def __init__(self, network_manager: NetworkManager):
        """
        Initialize the app launcher.
        
        Args:
            network_manager: NetworkManager instance for communication with SUT
        """
        self.network_manager = network_manager
        logger.info("AppLauncher initialized")
    
    def launch(self, app_path: str, process_id: str = '', startup_wait: int = 15) -> bool:
        """
        Launch an app on the SUT.

        Args:
            app_path: Path to the app executable or Steam app ID on the SUT
            process_id: Optional process name to wait for after launch (e.g., 'Launcher', 'App')
            startup_wait: Maximum seconds to wait for process to appear (default: 15)

        Returns:
            True if the app was successfully launched

        Raises:
            RuntimeError: If the app fails to launch
        """
        try:
            # Send launch command to SUT with process tracking metadata
            response = self.network_manager.launch_game(app_path, process_id, startup_wait) # NOTE: network method still launch_game for now

            # Check response
            status = response.get("status")
            if status == "success":
                # Parse detailed status
                proc_name = response.get("game_process_name", "Unknown")
                proc_pid = response.get("game_process_pid", "N/A")
                fg_confirmed = response.get("foreground_confirmed", False)
                launch_method = response.get("launch_method", "unknown")
                
                logger.info(f"App launched successfully: {app_path}")
                logger.info(f"  - Launch Method: {launch_method}")
                logger.info(f"  - Process Detected: {proc_name} (PID: {proc_pid})")
                logger.info(f"  - Foreground Confirmed: {fg_confirmed}")
                return True
            elif status == "warning":
                 # Treat warning as failure for strict foreground enforcement
                 warning_msg = response.get("warning", "Unknown warning")
                 logger.error(f"App launch warning (treating as failure): {warning_msg}")
                 raise RuntimeError(f"App launch failed: {warning_msg}")
            else:
                error_msg = response.get("error", "Unknown error")
                logger.error(f"Failed to launch app: {error_msg}")
                raise RuntimeError(f"App launch failed: {error_msg}")

        except Exception as e:
            logger.error(f"Error launching app: {str(e)}")
            raise RuntimeError(f"App launch error: {str(e)}")
    
    def terminate(self) -> bool:
        """
        Terminate the currently running app on the SUT.
        
        Returns:
            True if the app was successfully terminated
        
        Raises:
            RuntimeError: If the app fails to terminate
        """
        try:
            # Send terminate command to SUT
            response = self.network_manager.send_action({
                "type": "terminate_game" # NOTE: SUT action still terminate_game for now
            })
            
            # Check response
            if response.get("status") == "success":
                logger.info("App terminated successfully")
                return True
            else:
                error_msg = response.get("error", "Unknown error")
                logger.error(f"Failed to terminate app: {error_msg}")
                raise RuntimeError(f"App termination failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error terminating app: {str(e)}")
            raise RuntimeError(f"App termination error: {str(e)}")