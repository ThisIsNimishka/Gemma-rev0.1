"""
Multi-SUT GUI Application for Game UI Navigation Automation Tool
Manages multiple System Under Test (SUT) machines simultaneously.
Each SUT runs independently with its own configuration and logging.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
import queue
import yaml
import json
from pathlib import Path
from datetime import datetime

# Add logging handler for GUI
class QueueHandler(logging.Handler):
    """Send logging records to a queue"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

class HybridConfigParser:
    """Handles loading and parsing both state machine and step-based YAML configurations."""

    def __init__(self, config_path: str):
        """Initialize the hybrid config parser."""
        self.config_path = config_path
        self.config = self._load_config()
        self.config_type = self._detect_config_type()
        self._validate_config()

        # Extract game metadata
        self.game_name = self.config.get("metadata", {}).get("game_name", "Unknown Game")
        logging.getLogger(__name__).info(f"HybridConfigParser initialized for {self.game_name} using {config_path} (type: {self.config_type})")

    def _load_config(self):
        """Load the YAML configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML config: {str(e)}")

    def _detect_config_type(self):
        """Detect whether this is a step-based or state machine configuration."""
        if "steps" in self.config:
            return "steps"
        elif "states" in self.config:
            # State machine config - transitions may be at root or nested in states
            return "state_machine"
        else:
            logging.getLogger(__name__).warning("Could not determine config type, defaulting to state_machine")
            return "state_machine"

    def _validate_config(self):
        """Validate the configuration structure based on detected type."""
        if self.config_type == "steps":
            return self._validate_steps_config()
        else:
            return self._validate_state_machine_config()

    def _validate_steps_config(self):
        """Validate step-based configuration."""
        if "steps" not in self.config:
            raise ValueError("Invalid config: missing 'steps' section")

        steps = self.config.get("steps", {})
        if not isinstance(steps, dict) or not steps:
            raise ValueError("Invalid config: steps section must be a non-empty dictionary")

        return True

    def _validate_state_machine_config(self):
        """Validate state machine configuration."""
        # Only states is strictly required - transitions can be nested in states
        required_sections = ["states", "initial_state", "target_state"]
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Invalid config: missing '{section}' section")

        return True

    def get_config(self):
        """Get the parsed configuration."""
        return self.config

    def get_config_type(self):
        """Get the detected configuration type."""
        return self.config_type

    def is_step_based(self):
        """Check if this is a step-based configuration."""
        return self.config_type == "steps"

    def get_state_definition(self, state_name: str):
        """Get the definition for a specific state (state machine configs only)."""
        if self.config_type != "state_machine":
            return None
        states = self.config.get("states", {})
        return states.get(state_name)

    def get_game_metadata(self):
        """Get game metadata from the configuration."""
        return self.config.get("metadata", {})


class SUTController:
    """Controls automation for a single SUT machine."""

    def __init__(self, name, ip, port, config_path="", game_path=""):
        """Initialize SUT controller."""
        self.name = name
        self.ip = ip
        self.port = port
        self.config_path = config_path
        self.game_path = game_path

        # Run iteration settings (per SUT)
        self.run_count = 3       # Number of iterations to run
        self.run_delay = 30      # Delay in seconds between runs

        # Threading
        self.thread = None
        self.stop_event = threading.Event()

        # Logging
        self.log_queue = queue.Queue()
        self.logger = None
        self.queue_handler = None  # Initialize to None to prevent duplicates

        # Status tracking
        self.status = "Idle"  # Idle, Running, Completed, Failed, Stopped, Error
        self.completed_steps = 0  # Track completed steps for X/Y display
        self.total_steps = 0      # Total steps in config
        self.current_step = ""

        # Run iteration tracking
        self.current_run = 0      # Current run number (for iterations)
        self.total_runs = 1       # Total runs to execute

        # Run directory
        self.current_run_dir = None

    def setup_logger(self, log_level="INFO"):
        """Setup logger for this SUT - captures ALL module logs."""
        # Validate and convert log level string to logging constant
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level not in valid_levels:
            log_level = "INFO"  # Fallback to INFO if invalid

        logger_name = f"SUT-{self.name}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, log_level))

        # CRITICAL: Disable propagation to prevent duplicate logs
        # Without this, logs from self.logger would go to BOTH self.logger handler AND root_logger handler
        self.logger.propagate = False

        # Remove existing handlers from this logger
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # IMPORTANT: Remove ALL QueueHandlers from root logger to prevent duplicates
        # This is more aggressive than just removing our handler
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, QueueHandler):
                root_logger.removeHandler(handler)

        # Queue handler for GUI
        queue_handler = QueueHandler(self.log_queue)
        queue_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                           datefmt='%H:%M:%S')
        queue_handler.setFormatter(queue_formatter)
        self.logger.addHandler(queue_handler)

        # IMPORTANT: Add queue handler to root logger to capture ALL module logs
        # This ensures logs from SimpleAutomation, NetworkManager, etc. are captured
        root_logger.addHandler(queue_handler)
        root_logger.setLevel(getattr(logging, log_level))

        # Store queue handler reference so we can remove it later
        self.queue_handler = queue_handler

        return self.logger

    def start_automation(self, shared_settings):
        """Start automation in a new thread."""
        if self.thread and self.thread.is_alive():
            self.logger.warning(f"Automation already running for {self.name}")
            return False

        if not self.config_path:
            self.logger.error("No config file specified")
            self.status = "Error"
            return False

        self.stop_event.clear()
        self.status = "Running"
        self.completed_steps = 0
        self.current_run = 0
        self.total_runs = self.run_count  # Use controller's own run_count
        self.thread = threading.Thread(
            target=self._run_automation,
            args=(shared_settings,),
            daemon=True
        )
        self.thread.start()
        return True

    def stop_automation(self):
        """Stop automation."""
        if self.thread and self.thread.is_alive():
            self.logger.info(f"Stopping automation for {self.name}")
            self.stop_event.set()
            self.status = "Stopped"
            return True
        return False

    def _run_automation(self, shared_settings):
        """Main automation logic (runs in separate thread)."""
        try:
            self.setup_logger(shared_settings.get("log_level", "INFO"))
            self.logger.info(f"Starting automation for {self.name}")
            self.logger.info(f"Config: {self.config_path}")
            self.logger.info(f"SUT: {self.ip}:{self.port}")

            # Load config
            try:
                config_parser = HybridConfigParser(self.config_path)
                config = config_parser.get_config()
                config_type = config_parser.get_config_type()
                self.logger.info(f"Config type: {config_type}")
            except Exception as e:
                self.logger.error(f"Failed to load config: {str(e)}")
                self.status = "Failed"
                return

            # Create batch folder for all runs
            batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            game_name = config_parser.game_name
            sut_dir = f"logs/{self.name}"
            os.makedirs(sut_dir, exist_ok=True)
            batch_dir = f"{sut_dir}/batch_{batch_timestamp}"
            os.makedirs(batch_dir, exist_ok=True)

            # Loop through runs using controller's own settings
            run_count = self.run_count
            run_delay = self.run_delay

            for run_num in range(1, run_count + 1):
                # Check for stop event before each run
                if self.stop_event.is_set():
                    self.logger.info(f"Automation stopped by user before run {run_num}")
                    self.status = "Stopped"
                    return

                self.current_run = run_num
                self.logger.info(f"========================================")
                self.logger.info(f"Starting Run {run_num}/{run_count}")
                self.logger.info(f"========================================")

                # Run appropriate automation type with batch_dir
                if config_parser.is_step_based():
                    self._run_simple_automation(config_parser, config, shared_settings, batch_dir, run_num)
                else:
                    self._run_state_machine_automation(config_parser, config, shared_settings, batch_dir, run_num)

                # Check if stopped or failed during run
                if self.stop_event.is_set():
                    self.logger.info(f"Automation stopped during run {run_num}")
                    self.status = "Stopped"
                    return

                if self.status == "Failed":
                    self.logger.error(f"Run {run_num} failed, stopping batch")
                    return

                # Delay between runs (except after last run)
                if run_num < run_count and run_delay > 0:
                    self.logger.info(f"Waiting {run_delay} seconds before next run...")
                    for _ in range(run_delay):
                        if self.stop_event.is_set():
                            self.logger.info("Automation stopped during delay")
                            self.status = "Stopped"
                            return
                        time.sleep(1)

            # All runs completed successfully
            if self.status != "Failed" and self.status != "Stopped":
                self.status = "Completed"
                self.logger.info(f"========================================")
                self.logger.info(f"All {run_count} runs completed successfully!")
                self.logger.info(f"========================================")

        except Exception as e:
            self.logger.error(f"Automation failed: {str(e)}", exc_info=True)
            self.status = "Failed"

        finally:
            # Cleanup queue handler from root logger after ALL runs complete
            if hasattr(self, 'queue_handler') and self.queue_handler:
                try:
                    root_logger = logging.getLogger()
                    root_logger.removeHandler(self.queue_handler)
                except Exception as e:
                    pass  # Ignore cleanup errors

    def _run_simple_automation(self, config_parser, config, shared_settings, batch_dir, run_num):
        """Run step-based automation."""
        try:
            # Import required modules
            from modules.network import NetworkManager
            from modules.screenshot import ScreenshotManager
            from modules.gemma_client import GemmaClient
            from modules.qwen_client import QwenClient
            from modules.omniparser_client import OmniparserClient
            from modules.annotator import Annotator
            from modules.simple_automation import SimpleAutomation
            from modules.game_launcher import GameLauncher

            # Create run-specific directory within batch folder
            run_dir = f"{batch_dir}/run_{run_num}"
            os.makedirs(run_dir, exist_ok=True)
            os.makedirs(f"{run_dir}/screenshots", exist_ok=True)
            os.makedirs(f"{run_dir}/annotated", exist_ok=True)

            self.current_run_dir = run_dir

            # Set up run-specific logging
            run_log_file = f"{run_dir}/automation.log"
            run_file_handler = logging.FileHandler(run_log_file)
            run_file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            run_file_handler.setFormatter(run_file_formatter)
            self.logger.addHandler(run_file_handler)

            self.logger.info(f"Created run directory: {run_dir}")

            # Initialize components
            self.logger.info(f"Connecting to SUT at {self.ip}:{self.port}")
            network = NetworkManager(self.ip, int(self.port))

            self.logger.info("Initializing components...")
            screenshot_mgr = ScreenshotManager(network)

            # Initialize vision model based on shared settings
            vision_model_type = shared_settings.get("vision_model", "omniparser")
            if vision_model_type == 'gemma':
                self.logger.info("Using Gemma for UI detection")
                vision_model = GemmaClient(shared_settings.get("lm_studio_url"))
            elif vision_model_type == 'qwen':
                self.logger.info("Using Qwen VL for UI detection")
                vision_model = QwenClient(shared_settings.get("lm_studio_url"))
            elif vision_model_type == 'omniparser':
                self.logger.info("Using Omniparser for UI detection")
                vision_model = OmniparserClient(shared_settings.get("omniparser_url"))

            annotator = Annotator()
            game_launcher = GameLauncher(network)

            # Get game metadata
            game_metadata = config_parser.get_game_metadata()
            self.logger.info(f"Game metadata loaded: {game_metadata}")
            startup_wait = game_metadata.get("startup_wait", 30)
            process_id = game_metadata.get("process_id", '')

            try:
                # Launch game if path provided
                if self.game_path:
                    self.logger.info(f"Launching game from: {self.game_path}")
                    # Pass process_id and startup_wait to enable process tracking on SUT
                    game_launcher.launch(self.game_path, process_id, startup_wait)

                    # Wait for game to initialize
                    self.logger.info(f"Waiting {startup_wait} seconds for game to initialize...")
                    for i in range(startup_wait):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                        self.current_step = f"Initializing ({startup_wait-i}s)"
                else:
                    self.logger.info("No game path provided, assuming game is already running")

                if self.stop_event.is_set():
                    self.logger.info("Automation stopped during initialization")
                    self.status = "Stopped"
                    return

                # Start SimpleAutomation
                self.logger.info("Starting SimpleAutomation...")
                simple_auto = SimpleAutomation(
                    config_path=self.config_path,
                    network=network,
                    screenshot_mgr=screenshot_mgr,
                    vision_model=vision_model,
                    stop_event=self.stop_event,
                    run_dir=run_dir,
                    annotator=annotator,
                    progress_callback=self  # Pass controller to track step progress
                )

                # Run automation
                success = simple_auto.run()

                # Update status based on result
                if success:
                    self.status = "Completed"
                    self.logger.info("Automation completed successfully")
                elif self.stop_event.is_set():
                    self.status = "Stopped"
                    self.logger.info("Automation stopped by user")
                else:
                    self.status = "Failed"
                    self.logger.error("Automation failed")

            except Exception as e:
                self.logger.error(f"Error in automation execution: {str(e)}", exc_info=True)
                self.status = "Failed"

            finally:
                # Cleanup per-run resources (NOT queue_handler - that's cleaned up after all runs)
                if 'network' in locals():
                    network.close()
                if 'vision_model' in locals() and hasattr(vision_model, 'close'):
                    vision_model.close()
                if 'run_file_handler' in locals():
                    self.logger.removeHandler(run_file_handler)

        except Exception as e:
            self.logger.error(f"SimpleAutomation failed: {str(e)}", exc_info=True)
            self.status = "Failed"

    def _run_state_machine_automation(self, config_parser, config, shared_settings, batch_dir, run_num):
        """Run state machine automation."""
        try:
            # Import required modules
            from modules.network import NetworkManager
            from modules.screenshot import ScreenshotManager
            from modules.gemma_client import GemmaClient
            from modules.qwen_client import QwenClient
            from modules.omniparser_client import OmniparserClient
            from modules.annotator import Annotator
            from modules.decision_engine import DecisionEngine
            from modules.game_launcher import GameLauncher

            # Create run-specific directory within batch folder
            run_dir = f"{batch_dir}/run_{run_num}"
            os.makedirs(run_dir, exist_ok=True)
            os.makedirs(f"{run_dir}/screenshots", exist_ok=True)
            os.makedirs(f"{run_dir}/annotated", exist_ok=True)

            self.current_run_dir = run_dir

            # Setup logging
            run_log_file = f"{run_dir}/automation.log"
            run_file_handler = logging.FileHandler(run_log_file)
            run_file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            run_file_handler.setFormatter(run_file_formatter)
            self.logger.addHandler(run_file_handler)

            self.logger.info(f"Created run directory: {run_dir}")

            # Initialize components
            self.logger.info(f"Connecting to SUT at {self.ip}:{self.port}")
            network = NetworkManager(self.ip, int(self.port))

            screenshot_mgr = ScreenshotManager(network)

            # Initialize vision model
            vision_model_type = shared_settings.get("vision_model", "omniparser")
            if vision_model_type == 'gemma':
                vision_model = GemmaClient(shared_settings.get("lm_studio_url"))
            elif vision_model_type == 'qwen':
                vision_model = QwenClient(shared_settings.get("lm_studio_url"))
            elif vision_model_type == 'omniparser':
                vision_model = OmniparserClient(shared_settings.get("omniparser_url"))

            annotator = Annotator()
            game_launcher = GameLauncher(network)

            # Get game metadata
            game_metadata = config_parser.get_game_metadata()
            startup_wait = game_metadata.get("startup_wait", 30)
            process_id = game_metadata.get("process_id", '')

            try:
                # Launch game if path provided
                if self.game_path:
                    self.logger.info(f"Launching game from: {self.game_path}")
                    # Pass process_id and startup_wait to enable process tracking on SUT
                    game_launcher.launch(self.game_path, process_id, startup_wait)

                    for i in range(startup_wait):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                        self.current_step = f"Initializing ({startup_wait-i}s)"

                if self.stop_event.is_set():
                    self.status = "Stopped"
                    return

                # Create decision engine
                self.logger.info("Starting state machine automation...")
                decision_engine = DecisionEngine(
                    config,
                    network,
                    screenshot_mgr,
                    vision_model,
                    annotator,
                    shared_settings.get("max_iterations", 50),
                    run_dir
                )

                # Run automation
                success = decision_engine.run(self.stop_event)

                if success:
                    self.status = "Completed"
                elif self.stop_event.is_set():
                    self.status = "Stopped"
                else:
                    self.status = "Failed"

            except Exception as e:
                self.logger.error(f"Error in state machine execution: {str(e)}", exc_info=True)
                self.status = "Failed"

            finally:
                if 'network' in locals():
                    network.close()
                if 'vision_model' in locals() and hasattr(vision_model, 'close'):
                    vision_model.close()
                if 'run_file_handler' in locals():
                    self.logger.removeHandler(run_file_handler)

        except Exception as e:
            self.logger.error(f"State machine automation failed: {str(e)}", exc_info=True)
            self.status = "Failed"

    def get_status_color(self):
        """Get color for status indicator."""
        status_colors = {
            "Idle": "yellow",
            "Running": "green",
            "Completed": "blue",
            "Failed": "red",
            "Stopped": "orange",
            "Error": "red",
            "Not Connected": "red"
        }
        return status_colors.get(self.status, "yellow")

    def to_dict(self):
        """Convert to dictionary for saving."""
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "config_path": self.config_path,
            "game_path": self.game_path,
            "run_count": self.run_count,
            "run_delay": self.run_delay
        }

    @staticmethod
    def from_dict(data):
        """Create SUTController from dictionary."""
        controller = SUTController(
            name=data.get("name", "SUT"),
            ip=data.get("ip", ""),
            port=data.get("port", 8080),
            config_path=data.get("config_path", ""),
            game_path=data.get("game_path", "")
        )
        # Restore run settings
        controller.run_count = data.get("run_count", 3)
        controller.run_delay = data.get("run_delay", 30)
        return controller


class MultiSUTGUI:
    """Main GUI for multi-SUT automation control."""

    def __init__(self, root):
        """Initialize the multi-SUT GUI."""
        self.root = root
        self.root.title("Katana Multi-SUT Automator | Ver 1.0 | Alpha")
        self.root.geometry("1600x900")
        self.root.minsize(1200, 700)

        # SUT controllers
        self.sut_controllers = {}  # {name: SUTController}
        self.sut_tabs = {}  # {name: tab_frame}
        self.sut_widgets = {}  # {name: {widget_dict}}

        # Shared settings
        self.vision_model = tk.StringVar(value="omniparser")
        self.omniparser_url = tk.StringVar(value="http://localhost:9000")
        self.lm_studio_url = tk.StringVar(value="http://127.0.0.1:1234")
        self.max_iterations = tk.StringVar(value="50")
        self.log_level = tk.StringVar(value="INFO")

        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)

        # Create GUI
        self.create_master_panel()
        self.create_sut_tabs()

        # Start GUI update loop
        self.root.after(100, self.update_gui)

    def create_master_panel(self):
        """Create the master control panel at the top."""
        # Master frame
        master_frame = ttk.LabelFrame(self.root, text="Master Control Panel", padding="10")
        master_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Shared settings section
        settings_frame = ttk.LabelFrame(master_frame, text="Shared Vision Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Vision model selection
        model_row = ttk.Frame(settings_frame)
        model_row.pack(fill=tk.X, pady=5)
        ttk.Label(model_row, text="Vision Model:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(model_row, text="Omniparser", variable=self.vision_model,
                       value="omniparser", command=self.on_vision_model_change).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(model_row, text="Gemma", variable=self.vision_model,
                       value="gemma", command=self.on_vision_model_change).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(model_row, text="Qwen VL", variable=self.vision_model,
                       value="qwen", command=self.on_vision_model_change).pack(side=tk.LEFT)

        # Queue manager to Omniparser
        omni_row = ttk.Frame(settings_frame)
        omni_row.pack(fill=tk.X, pady=5)
        ttk.Label(omni_row, text="Queue Manager -> Omniparser :").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(omni_row, textvariable=self.omniparser_url, width=30).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(omni_row, text="Test Connection", command=self.test_omniparser).pack(side=tk.LEFT, padx=(0, 10))
        self.omniparser_status_label = tk.Label(omni_row, text="Not Tested", foreground="gray", font=("TkDefaultFont", 10))
        self.omniparser_status_label.pack(side=tk.LEFT)

        # LM Studio URL
        lm_row = ttk.Frame(settings_frame)
        lm_row.pack(fill=tk.X, pady=5)
        ttk.Label(lm_row, text="LM Studio URL:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(lm_row, textvariable=self.lm_studio_url, width=30).pack(side=tk.LEFT, padx=(0, 10))

        # Max iterations
        iter_row = ttk.Frame(settings_frame)
        iter_row.pack(fill=tk.X, pady=5)
        ttk.Label(iter_row, text="Max Iterations:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(iter_row, textvariable=self.max_iterations, width=10).pack(side=tk.LEFT)

        # Log level
        log_row = ttk.Frame(settings_frame)
        log_row.pack(fill=tk.X, pady=5)
        ttk.Label(log_row, text="Log Level:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(log_row, textvariable=self.log_level,
                     values=["DEBUG", "INFO", "WARNING", "ERROR"],
                     state='readonly', width=10).pack(side=tk.LEFT)

        # Multi-SUT controls section
        controls_frame = ttk.LabelFrame(master_frame, text="Multi-SUT Controls", padding="10")
        controls_frame.pack(fill=tk.X)

        button_row = ttk.Frame(controls_frame)
        button_row.pack(fill=tk.X)

        ttk.Button(button_row, text="+ Add SUT", command=self.add_sut_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="- Remove SUT", command=self.remove_current_sut).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="Start All", command=self.start_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="Stop All", command=self.stop_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="Load Config", command=self.load_multi_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="Save Config", command=self.save_multi_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="Clear All Logs", command=self.clear_all_logs).pack(side=tk.LEFT, padx=5)

    def create_sut_tabs(self):
        """Create the SUT tabs section at the bottom."""
        # Tabs frame
        tabs_frame = ttk.Frame(self.root)
        tabs_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Notebook for tabs
        self.notebook = ttk.Notebook(tabs_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def add_sut_dialog(self):
        """Show dialog to add a new SUT."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New SUT")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Dialog content
        content_frame = ttk.Frame(dialog, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(content_frame, text="SUT Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=f"SUT-{len(self.sut_controllers)+1}")
        ttk.Entry(content_frame, textvariable=name_var, width=30).grid(row=0, column=1, pady=5, padx=(10, 0))

        # IP
        ttk.Label(content_frame, text="IP Address:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ip_var = tk.StringVar(value="192.168.50.230")
        ttk.Entry(content_frame, textvariable=ip_var, width=30).grid(row=1, column=1, pady=5, padx=(10, 0))

        # Port
        ttk.Label(content_frame, text="Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        port_var = tk.StringVar(value="8080")
        ttk.Entry(content_frame, textvariable=port_var, width=30).grid(row=2, column=1, pady=5, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(content_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)

        def on_add():
            name = name_var.get().strip()
            ip = ip_var.get().strip()
            port = port_var.get().strip()

            # Validate
            if not name:
                messagebox.showerror("Error", "SUT name is required")
                return
            if name in self.sut_controllers:
                messagebox.showerror("Error", f"SUT '{name}' already exists")
                return
            if not ip:
                messagebox.showerror("Error", "IP address is required")
                return
            if not port:
                messagebox.showerror("Error", "Port is required")
                return

            try:
                port = int(port)
            except ValueError:
                messagebox.showerror("Error", "Port must be a number")
                return

            # Create SUT controller (config and game path will be set in the tab)
            self.add_sut(name, ip, port, "", "")
            dialog.destroy()

        ttk.Button(button_frame, text="Add", command=on_add, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def add_sut(self, name, ip, port, config_path="", game_path=""):
        """Add a new SUT controller and tab."""
        # Create controller
        controller = SUTController(name, ip, port, config_path, game_path)
        self.sut_controllers[name] = controller

        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=f"{name}: {ip}")
        self.sut_tabs[name] = tab_frame

        # Create widgets for this tab
        self._create_sut_tab_content(name, tab_frame, controller)

        # Auto-load game path if config is provided
        if config_path:
            widgets = self.sut_widgets[name]
            self._auto_load_game_path(controller, widgets['game_var'])

        # Switch to new tab
        self.notebook.select(tab_frame)

    def _create_sut_tab_content(self, name, tab_frame, controller):
        """Create the content for a SUT tab."""
        # Store widget references
        widgets = {}

        # Main container with border to distinguish tabs
        main_container = tk.Frame(tab_frame, relief="groove", borderwidth=2, background="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configuration frame
        config_frame = ttk.LabelFrame(main_container, text="SUT Configuration", padding="10")
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # Row 1: Name, IP, Port, Test Connection
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="Name:").pack(side=tk.LEFT, padx=(0, 5))
        name_label = tk.Label(row1, text=controller.name, font=("TkDefaultFont", 10), relief="sunken", width=15, anchor="w")
        name_label.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(row1, text="IP:").pack(side=tk.LEFT, padx=(0, 5))
        ip_var = tk.StringVar(value=controller.ip)
        ip_entry = ttk.Entry(row1, textvariable=ip_var, width=15)
        ip_entry.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(row1, text="Port:").pack(side=tk.LEFT, padx=(0, 5))
        port_var = tk.StringVar(value=str(controller.port))
        port_entry = ttk.Entry(row1, textvariable=port_var, width=8)
        port_entry.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(row1, text="Test Connection", command=lambda: self._test_connection(controller)).pack(side=tk.LEFT)

        widgets['ip_var'] = ip_var
        widgets['port_var'] = port_var

        # Define game_var early so it's available for callbacks and preview updates
        game_var = tk.StringVar(value=controller.game_path)

        # Row 2: Config dropdown selector
        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Config:").pack(side=tk.LEFT, padx=(0, 5))

        # Load available configs
        config_dict = self._load_available_configs()
        config_names = list(config_dict.keys())

        config_selection_var = tk.StringVar()
        config_dropdown = ttk.Combobox(row2, textvariable=config_selection_var,
                                       values=config_names, state='readonly', width=40)
        config_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # Set initial selection if config path exists
        if controller.config_path:
            for name, path in config_dict.items():
                if path == controller.config_path:
                    config_selection_var.set(name)
                    break

        def on_config_select(event=None):
            selected_name = config_selection_var.get()
            if selected_name and selected_name in config_dict:
                config_path = config_dict[selected_name]
                controller.config_path = config_path
                # Update preview and auto-load game path
                self._update_config_preview(controller, config_preview_frame, game_var)

        config_dropdown.bind('<<ComboboxSelected>>', on_config_select)

        def refresh_configs():
            new_config_dict = self._load_available_configs()
            new_names = list(new_config_dict.keys())
            config_dropdown['values'] = new_names
            # Update the stored dict
            config_dict.clear()
            config_dict.update(new_config_dict)

        ttk.Button(row2, text="Refresh List", command=refresh_configs).pack(side=tk.LEFT)

        widgets['config_selection_var'] = config_selection_var
        widgets['config_dict'] = config_dict

        # Row 2b: Config details preview panel
        config_preview_frame = ttk.LabelFrame(config_frame, text="Config Details", padding="5")
        config_preview_frame.pack(fill=tk.X, pady=(5, 0))

        # Create preview labels (will be populated when config is selected)
        preview_text = tk.Text(config_preview_frame, height=5, wrap=tk.WORD, relief="flat",
                               background="#f0f0f0", font=("consolas", 8))
        preview_text.pack(fill=tk.BOTH, expand=True)
        preview_text.config(state='disabled')

        widgets['config_preview_text'] = preview_text
        widgets['config_preview_frame'] = config_preview_frame

        # Update preview if config already selected
        if controller.config_path:
            self._update_config_preview(controller, config_preview_frame, game_var)

        # Row 3: Game path
        row3 = ttk.Frame(config_frame)
        row3.pack(fill=tk.X, pady=5)
        ttk.Label(row3, text="Game Path:").pack(side=tk.LEFT, padx=(0, 5))
        # game_var already defined earlier (before Row 2) to avoid scope issues
        game_entry = ttk.Entry(row3, textvariable=game_var, width=50)
        game_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        ttk.Button(row3, text="Clear", command=lambda: game_var.set("")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(row3, text="Verify", command=lambda: self._verify_game_path(controller)).pack(side=tk.LEFT)

        widgets['game_var'] = game_var

        # Row 4: Run iteration settings
        row4 = ttk.Frame(config_frame)
        row4.pack(fill=tk.X, pady=5)
        ttk.Label(row4, text="Run Count:").pack(side=tk.LEFT, padx=(0, 5))
        run_count_var = tk.IntVar(value=controller.run_count)
        ttk.Spinbox(row4, from_=1, to=100, textvariable=run_count_var, width=8).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(row4, text="Delay Between Runs (sec):").pack(side=tk.LEFT, padx=(0, 5))
        run_delay_var = tk.IntVar(value=controller.run_delay)
        ttk.Spinbox(row4, from_=0, to=3600, textvariable=run_delay_var, width=8).pack(side=tk.LEFT)

        widgets['run_count_var'] = run_count_var
        widgets['run_delay_var'] = run_delay_var

        # Controls frame
        controls_frame = ttk.LabelFrame(main_container, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        button_row = ttk.Frame(controls_frame)
        button_row.pack(fill=tk.X)

        start_btn = ttk.Button(button_row, text="Start",
                               command=lambda: self._start_sut(controller))
        start_btn.pack(side=tk.LEFT, padx=5)
        widgets['start_btn'] = start_btn

        stop_btn = ttk.Button(button_row, text="Stop",
                             command=lambda: self._stop_sut(controller))
        stop_btn.pack(side=tk.LEFT, padx=5)
        widgets['stop_btn'] = stop_btn

        ttk.Button(button_row, text="Restart",
                  command=lambda: self._restart_sut(controller)).pack(side=tk.LEFT, padx=5)

        # Status frame
        status_frame = ttk.Frame(main_container)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        status_left = ttk.Frame(status_frame)
        status_left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(status_left, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        status_label = tk.Label(status_left, text="Idle", foreground="yellow", font=("TkDefaultFont", 10))
        status_label.pack(side=tk.LEFT, padx=(0, 20))
        widgets['status_label'] = status_label

        ttk.Button(status_frame, text="Export Logs",
                  command=lambda: self._export_logs(controller)).pack(side=tk.RIGHT)

        # Step progress display
        progress_frame = ttk.Frame(main_container)
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT, padx=(0, 5))
        steps_label = ttk.Label(progress_frame, text="Steps: 0/0")
        steps_label.pack(side=tk.LEFT, padx=(0, 15))
        widgets['steps_label'] = steps_label

        # Run iteration display (small text)
        run_label = ttk.Label(progress_frame, text="Run: 0/1", font=("TkDefaultFont", 8))
        run_label.pack(side=tk.LEFT)
        widgets['run_label'] = run_label

        # Logs frame
        logs_frame = ttk.LabelFrame(main_container, text="Logs", padding="10")
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        log_text = scrolledtext.ScrolledText(logs_frame, height=15, wrap=tk.WORD)
        log_text.pack(fill=tk.BOTH, expand=True)

        # Configure color tags for different log levels
        log_text.tag_configure("ERROR", foreground="#FF0000")      # Red
        log_text.tag_configure("WARNING", foreground="#FFA500")    # Orange
        log_text.tag_configure("INFO", foreground="#000000")       # Black
        log_text.tag_configure("DEBUG", foreground="#808080")      # Gray
        log_text.tag_configure("CRITICAL", foreground="#FF0000", background="#FFFF00")  # Red on yellow

        widgets['log_text'] = log_text

        # Store widgets
        self.sut_widgets[name] = widgets

    def _start_sut(self, controller):
        """Start automation for a SUT."""
        # Update controller properties from GUI
        widgets = self.sut_widgets[controller.name]
        controller.ip = widgets['ip_var'].get()
        controller.port = int(widgets['port_var'].get())
        # Config path is already updated from dropdown selection
        controller.game_path = widgets['game_var'].get()
        controller.run_count = widgets['run_count_var'].get()
        controller.run_delay = widgets['run_delay_var'].get()

        # Get shared settings
        shared_settings = {
            "vision_model": self.vision_model.get(),
            "omniparser_url": self.omniparser_url.get(),
            "lm_studio_url": self.lm_studio_url.get(),
            "max_iterations": int(self.max_iterations.get()),
            "log_level": self.log_level.get()
        }

        # Start automation
        if controller.start_automation(shared_settings):
            widgets['log_text'].insert(tk.END, f"Starting automation for {controller.name}...\n")
            widgets['log_text'].see(tk.END)
        else:
            messagebox.showwarning("Warning", f"Could not start automation for {controller.name}")

    def _stop_sut(self, controller):
        """Stop automation for a SUT."""
        controller.stop_automation()
        widgets = self.sut_widgets[controller.name]
        widgets['log_text'].insert(tk.END, f"Stopping automation for {controller.name}...\n")
        widgets['log_text'].see(tk.END)

    def _restart_sut(self, controller):
        """Restart automation for a SUT."""
        self._stop_sut(controller)
        time.sleep(1)
        self._start_sut(controller)

    def _test_connection(self, controller):
        """Test connection to a SUT."""
        widgets = self.sut_widgets[controller.name]
        ip = widgets['ip_var'].get()
        port = widgets['port_var'].get()

        try:
            import requests
            response = requests.get(f"http://{ip}:{port}/health", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Success", f"Connected to SUT at {ip}:{port}")
            else:
                messagebox.showerror("Error", f"SUT returned status {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {str(e)}")

    def _verify_game_path(self, controller):
        """Verify game path on SUT."""
        messagebox.showinfo("Info", "Game path verification not yet implemented")

    def _reload_config(self, controller, game_var):
        """Reload config file for SUT and auto-populate game path."""
        widgets = self.sut_widgets[controller.name]
        config_path = widgets['config_var'].get()

        if not config_path or not os.path.exists(config_path):
            messagebox.showerror("Error", "Config file not found")
            return

        try:
            config_parser = HybridConfigParser(config_path)
            # Auto-load game path from config
            self._auto_load_game_path(controller, game_var)
            messagebox.showinfo("Success", f"Config loaded: {config_parser.game_name} ({config_parser.config_type})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {str(e)}")

    def _auto_load_game_path(self, controller, game_var):
        """Auto-populate game path from config file metadata."""
        if not controller.config_path or not os.path.exists(controller.config_path):
            return

        try:
            # Load config and extract metadata
            config_parser = HybridConfigParser(controller.config_path)
            metadata = config_parser.get_game_metadata()

            # Get game path from metadata
            game_path_in_config = metadata.get("path", "")

            if game_path_in_config:
                # Auto-populate game path
                game_var.set(game_path_in_config)
                controller.game_path = game_path_in_config

                # Log to SUT's log queue if logger exists
                if controller.logger:
                    controller.logger.info(f"Auto-populated game path from config: {game_path_in_config}")
            else:
                # No path in config, clear if needed
                if not game_var.get():
                    game_var.set("")

        except Exception as e:
            # Silent fail - config might be loading
            pass

    def _load_available_configs(self):
        """Scan config/games folder and return dict of {game_name: file_path}."""
        config_dict = {}
        config_dir = "config/games"

        if not os.path.exists(config_dir):
            return config_dict

        try:
            for filename in os.listdir(config_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    filepath = os.path.join(config_dir, filename)
                    try:
                        # Parse config to get game name
                        config_parser = HybridConfigParser(filepath)
                        game_name = config_parser.game_name

                        # Use game name as key, if duplicate add filename
                        display_name = game_name
                        if display_name in config_dict:
                            display_name = f"{game_name} ({filename})"

                        config_dict[display_name] = filepath
                    except Exception as e:
                        # If parsing fails, use filename as fallback
                        config_dict[filename] = filepath

        except Exception as e:
            # If scanning fails, return empty dict
            pass

        return config_dict

    def _update_config_preview(self, controller, preview_frame, game_var):
        """Update the config preview panel with metadata."""
        widgets = self.sut_widgets[controller.name]
        preview_text = widgets['config_preview_text']

        if not controller.config_path or not os.path.exists(controller.config_path):
            preview_text.config(state='normal')
            preview_text.delete("1.0", tk.END)
            preview_text.insert("1.0", "No config selected")
            preview_text.config(state='disabled')
            return

        try:
            # Parse config
            config_parser = HybridConfigParser(controller.config_path)
            metadata = config_parser.get_game_metadata()
            config_type = config_parser.get_config_type()

            # Build preview text
            preview_lines = []
            preview_lines.append(f"Game Name:      {config_parser.game_name}")
            preview_lines.append(f"Config Type:    {'Step-based (SimpleAutomation)' if config_type == 'steps' else 'State Machine (DecisionEngine)'}")

            if metadata.get("resolution"):
                preview_lines.append(f"Resolution:     {metadata.get('resolution')}")
            if metadata.get("preset"):
                preview_lines.append(f"Preset:         {metadata.get('preset')}")
            if metadata.get("benchmark_duration"):
                preview_lines.append(f"Duration:       {metadata.get('benchmark_duration')} seconds")
            if metadata.get("path"):
                preview_lines.append(f"Game Path:      {metadata.get('path')}")

            preview_lines.append(f"File:           {controller.config_path}")

            # Update preview
            preview_text.config(state='normal')
            preview_text.delete("1.0", tk.END)
            preview_text.insert("1.0", "\n".join(preview_lines))
            preview_text.config(state='disabled')

            # Auto-load game path
            self._auto_load_game_path(controller, game_var)

        except Exception as e:
            preview_text.config(state='normal')
            preview_text.delete("1.0", tk.END)
            preview_text.insert("1.0", f"Error loading config: {str(e)}")
            preview_text.config(state='disabled')

    def _export_logs(self, controller):
        """Export logs for a SUT."""
        if not controller.current_run_dir:
            messagebox.showwarning("Warning", "No logs to export yet")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{controller.name}_logs.txt"
        )

        if filename:
            try:
                widgets = self.sut_widgets[controller.name]
                log_content = widgets['log_text'].get("1.0", tk.END)
                with open(filename, 'w') as f:
                    f.write(log_content)
                messagebox.showinfo("Success", f"Logs exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export logs: {str(e)}")

    def start_all(self):
        """Start automation on all SUTs."""
        if not self.sut_controllers:
            messagebox.showwarning("Warning", "No SUTs configured")
            return

        shared_settings = {
            "vision_model": self.vision_model.get(),
            "omniparser_url": self.omniparser_url.get(),
            "lm_studio_url": self.lm_studio_url.get(),
            "max_iterations": int(self.max_iterations.get()),
            "log_level": self.log_level.get()
        }

        for name, controller in self.sut_controllers.items():
            if controller.status == "Idle":
                # Update controller from GUI widgets
                widgets = self.sut_widgets.get(name)
                if widgets:
                    controller.run_count = widgets['run_count_var'].get()
                    controller.run_delay = widgets['run_delay_var'].get()
                controller.start_automation(shared_settings)

    def stop_all(self):
        """Stop automation on all SUTs."""
        for controller in self.sut_controllers.values():
            controller.stop_automation()

    def clear_all_logs(self):
        """Clear logs on all tabs."""
        for name, widgets in self.sut_widgets.items():
            widgets['log_text'].delete("1.0", tk.END)

    def remove_current_sut(self):
        """Remove the currently selected SUT tab."""
        if not self.sut_controllers:
            messagebox.showwarning("Warning", "No SUTs to remove")
            return

        # Get currently selected tab
        try:
            current_tab_index = self.notebook.index(self.notebook.select())
            current_tab = self.notebook.select()

            # Find the SUT name for this tab
            sut_name = None
            for name, tab in self.sut_tabs.items():
                if str(tab) == str(current_tab):
                    sut_name = name
                    break

            if not sut_name:
                messagebox.showwarning("Warning", "No SUT selected")
                return

            # Confirm removal
            if messagebox.askyesno("Confirm Removal", f"Remove SUT '{sut_name}'?\n\nThis will stop any running automation."):
                self._remove_sut(sut_name)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove SUT: {str(e)}")

    def save_multi_config(self):
        """Save multi-SUT configuration to JSON."""
        filename = filedialog.asksaveasfilename(
            title="Save Multi-SUT Config",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="multi_sut_config.json"
        )

        if not filename:
            return

        config = {
            "version": "1.0",
            "shared_settings": {
                "vision_model": self.vision_model.get(),
                "omniparser_url": self.omniparser_url.get(),
                "lm_studio_url": self.lm_studio_url.get(),
                "max_iterations": int(self.max_iterations.get()),
                "log_level": self.log_level.get()
            },
            "suts": [controller.to_dict() for controller in self.sut_controllers.values()]
        }

        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Success", f"Configuration saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")

    def load_multi_config(self):
        """Load multi-SUT configuration from JSON."""
        filename = filedialog.askopenfilename(
            title="Load Multi-SUT Config",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="."
        )

        if not filename:
            return

        try:
            with open(filename, 'r') as f:
                config = json.load(f)

            # Load shared settings
            shared = config.get("shared_settings", {})
            self.vision_model.set(shared.get("vision_model", "omniparser"))
            self.omniparser_url.set(shared.get("omniparser_url", "http://localhost:9000"))
            self.lm_studio_url.set(shared.get("lm_studio_url", "http://127.0.0.1:1234"))
            self.max_iterations.set(str(shared.get("max_iterations", 50)))
            self.log_level.set(shared.get("log_level", "INFO"))

            # Clear existing SUTs
            for name in list(self.sut_controllers.keys()):
                self._remove_sut(name)

            # Load SUTs
            for sut_data in config.get("suts", []):
                controller = SUTController.from_dict(sut_data)
                self.sut_controllers[controller.name] = controller

                # Create tab
                tab_frame = ttk.Frame(self.notebook)
                self.notebook.add(tab_frame, text=f"{controller.name}: {controller.ip}")
                self.sut_tabs[controller.name] = tab_frame

                # Create widgets
                self._create_sut_tab_content(controller.name, tab_frame, controller)

            messagebox.showinfo("Success", f"Loaded {len(config.get('suts', []))} SUTs from {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {str(e)}")

    def _remove_sut(self, name):
        """Remove a SUT controller and tab."""
        if name not in self.sut_controllers:
            return

        # Stop automation if running
        self.sut_controllers[name].stop_automation()

        # Remove tab
        if name in self.sut_tabs:
            tab = self.sut_tabs[name]
            self.notebook.forget(tab)
            del self.sut_tabs[name]

        # Remove widgets
        if name in self.sut_widgets:
            del self.sut_widgets[name]

        # Remove controller
        del self.sut_controllers[name]

    def on_vision_model_change(self):
        """Handle vision model selection change."""
        # Update UI based on selection
        pass

    def test_omniparser(self):
        """Test connection to Omniparser server."""
        try:
            import requests
            response = requests.get(f"{self.omniparser_url.get()}/probe", timeout=5)
            if response.status_code == 200:
                self.omniparser_status_label.config(text="Connected", foreground="green")
                messagebox.showinfo("Success", "Connected to Omniparser server")
            else:
                self.omniparser_status_label.config(text="Failed", foreground="red")
                messagebox.showerror("Error", f"Server returned status {response.status_code}")
        except Exception as e:
            self.omniparser_status_label.config(text="Failed", foreground="red")
            messagebox.showerror("Error", f"Failed to connect: {str(e)}")

    def on_tab_changed(self, event):
        """Handle tab change event."""
        pass

    def update_gui(self):
        """Periodic GUI update - poll log queues and update status."""
        # Update each SUT
        for name, controller in self.sut_controllers.items():
            if name not in self.sut_widgets:
                continue

            widgets = self.sut_widgets[name]

            # Update status
            status_label = widgets['status_label']
            status_label.config(text=controller.status, foreground=controller.get_status_color())

            # Update step progress
            steps_label = widgets['steps_label']
            steps_label.config(text=f"Steps: {controller.completed_steps}/{controller.total_steps}")

            # Update run iteration progress
            run_label = widgets['run_label']
            run_label.config(text=f"Run: {controller.current_run}/{controller.total_runs}")

            # Update tab title with status indicator
            tab_text = f"{controller.name}: {controller.ip}"
            if controller.status == "Running":
                tab_text += " ●"
            elif controller.status == "Failed" or controller.status == "Error":
                tab_text += " ●"

            # Find tab index and update
            for idx in range(self.notebook.index("end")):
                if self.notebook.tab(idx, "text").startswith(controller.name):
                    self.notebook.tab(idx, text=tab_text)
                    break

            # Poll log queue
            log_text = widgets['log_text']
            while not controller.log_queue.empty():
                try:
                    record = controller.log_queue.get_nowait()
                    msg = record.getMessage()
                    timestamp = time.strftime('%H:%M:%S', time.localtime(record.created))
                    log_line = f"{timestamp} - {record.name} - {record.levelname} - {msg}\n"

                    # Insert log line with color tag based on level
                    tag = record.levelname if record.levelname in ["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"] else "INFO"
                    log_text.insert(tk.END, log_line, tag)
                    log_text.see(tk.END)
                except queue.Empty:
                    break

        # Schedule next update
        self.root.after(100, self.update_gui)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = MultiSUTGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
