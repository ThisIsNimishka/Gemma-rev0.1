"""
Stopwatch module for tracking automation workflow timing.
Provides visual timing data for operators to see workflow performance.
"""

import time
import json
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Stopwatch:
    """Tracks timing for automation workflow steps."""
    
    def __init__(self):
        """Initialize the stopwatch."""
        self.start_times: Dict[str, float] = {}
        self.durations: Dict[str, float] = {}
        self.workflow_start = time.perf_counter()
        logger.info("⏱️  Stopwatch initialized")
    
    def start(self, name: str) -> None:
        """
        Start a named timer.
        
        Args:
            name: Name of the timer (e.g., "Video_Export", "Model_Load")
        """
        self.start_times[name] = time.perf_counter()
        elapsed_since_workflow = time.perf_counter() - self.workflow_start
        logger.info(f"⏱️  Timer '{name}' started at T+{elapsed_since_workflow:.2f}s")
    
    def stop(self, name: str) -> float:
        """
        Stop a named timer and record duration.
        
        Args:
            name: Name of the timer to stop
            
        Returns:
            Duration in seconds, or 0.0 if timer wasn't started
        """
        if name not in self.start_times:
            logger.warning(f"⚠️  Timer '{name}' was stopped but never started")
            return 0.0
        
        duration = time.perf_counter() - self.start_times.pop(name)
        self.durations[name] = duration
        logger.info(f"⏱️  Timer '{name}' stopped: {duration:.4f}s ({self._format_duration(duration)})")
        return duration
    
    def get_duration(self, name: str) -> Optional[float]:
        """
        Get the recorded duration for a timer.
        
        Args:
            name: Name of the timer
            
        Returns:
            Duration in seconds, or None if not found
        """
        return self.durations.get(name)
    
    def get_all_durations(self) -> Dict[str, float]:
        """
        Get all recorded durations.
        
        Returns:
            Dictionary of timer names to durations
        """
        return self.durations.copy()
    
    def save_json(self, filepath: str) -> None:
        """
        Save timing data to JSON file.
        
        Args:
            filepath: Path to save the timing data
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_workflow_time": time.perf_counter() - self.workflow_start,
            "timings": self.durations
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"⏱️  Timing data saved to {filepath}")
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "1m 23s", "45s", "123ms")
        """
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
    
    def print_summary(self) -> None:
        """Print a visual summary of all timings to the console."""
        if not self.durations:
            logger.info("⏱️  No timing data recorded")
            return
        
        total_workflow = time.perf_counter() - self.workflow_start
        
        logger.info("")
        logger.info("╔════════════════════════════════════════════════════════════╗")
        logger.info("║                    TIMING SUMMARY                          ║")
        logger.info("╠════════════════════════════════════════════════════════════╣")
        
        # Sort by duration (longest first)
        sorted_timings = sorted(self.durations.items(), key=lambda x: x[1], reverse=True)
        
        for name, duration in sorted_timings:
            percentage = (duration / total_workflow) * 100 if total_workflow > 0 else 0
            bar = "█" * int(percentage / 2)  # Visual bar (50 chars max)
            logger.info(f"║ {name:30s} │ {duration:8.2f}s │ {percentage:5.1f}% │{bar}")
        
        logger.info("╠════════════════════════════════════════════════════════════╣")
        logger.info(f"║ Total Workflow Time: {total_workflow:.2f}s ({self._format_duration(total_workflow)})")
        logger.info("╚════════════════════════════════════════════════════════════╝")
        logger.info("")
