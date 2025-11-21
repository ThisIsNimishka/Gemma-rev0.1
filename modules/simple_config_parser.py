"""
Configuration parser for the simplified step-based YAML format.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SimpleConfigParser:
    """Handles loading and parsing the simplified step-based YAML configuration."""
    
    def __init__(self, config_path: str):
        """
        Initialize the simple config parser.
        
        Args:
            config_path: Path to the YAML configuration file
        
        Raises:
            FileNotFoundError: If the config file doesn't exist
            ValueError: If the config file is invalid
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
        
        # Extract basic metadata
        self.game_name = self.config.get("metadata", {}).get("game_name", "Unknown Game")
        logger.info(f"SimpleConfigParser initialized for {self.game_name} using {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the YAML configuration file.
        
        Returns:
            Parsed configuration as a dictionary
        
        Raises:
            FileNotFoundError: If the config file doesn't exist
            yaml.YAMLError: If the YAML is invalid
        """
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {str(e)}")
            raise
    
    def _validate_config(self) -> bool:
        """
        Validate the configuration structure.
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If the config is invalid
        """
        # Check for required sections
        if "steps" not in self.config:
            logger.error("Missing required 'steps' section in config")
            raise ValueError("Invalid config: missing 'steps' section")
        
        # Validate steps
        steps = self.config.get("steps", {})
        if not isinstance(steps, dict) or not steps:
            logger.error("Steps section must be a non-empty dictionary")
            raise ValueError("Invalid config: steps section must be a non-empty dictionary")
        
        # Validate each step
        for step_num, step in steps.items():
            if "description" not in step:
                logger.warning(f"Step {step_num} missing description")

            # Check that step has either:
            # 1. A 'find' section (for steps that need to locate UI elements)
            # 2. An 'action' section without 'find' (for action-only steps like wait, key press)
            has_find = "find" in step
            has_action = "action" in step

            if not has_find and not has_action:
                logger.error(f"Step {step_num} must have either 'find' or 'action' section")
                raise ValueError(f"Invalid step {step_num}: missing 'find' or 'action'")

            # Validate find section if present
            if has_find:
                find_section = step["find"]
                if not isinstance(find_section, dict):
                    logger.error(f"Step {step_num} 'find' must be a dictionary")
                    raise ValueError(f"Invalid step {step_num}: 'find' must be a dictionary")

                # Check for required fields in find section
                if "type" not in find_section and "text" not in find_section:
                    logger.warning(f"Step {step_num} 'find' should have 'type' and/or 'text'")

            # Validate action section if present
            if has_action:
                action_section = step["action"]
                if not isinstance(action_section, dict):
                    logger.error(f"Step {step_num} 'action' must be a dictionary")
                    raise ValueError(f"Invalid step {step_num}: 'action' must be a dictionary")

                # Check for action type
                if "type" not in action_section:
                    logger.error(f"Step {step_num} 'action' must have 'type' field")
                    raise ValueError(f"Invalid step {step_num}: 'action' missing 'type'")
        
        logger.info("Simple configuration validation successful")
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the parsed configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config
    
    def get_step(self, step_num: str) -> Optional[Dict[str, Any]]:
        """
        Get the definition for a specific step.
        
        Args:
            step_num: Step number as string
        
        Returns:
            Step definition dictionary or None if not found
        """
        steps = self.config.get("steps", {})
        return steps.get(step_num)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get game metadata from the configuration.
        
        Returns:
            Metadata dictionary with game information
        """
        return self.config.get("metadata", {})