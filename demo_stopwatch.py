"""
Demo script showing the visual stopwatch output.
Run this to see what timing looks like in the console.
"""

import time
import logging
from modules.stopwatch import Stopwatch

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def demo_timing():
    """Demonstrates the visual timing feature."""
    stopwatch = Stopwatch()
    
    # Simulate automation workflow
    print("\n🚀 Starting Demo Automation Workflow...\n")
    
    stopwatch.start("App_Launch")
    time.sleep(2.1)  # Simulate app launch
    stopwatch.stop("App_Launch")
   
    
    stopwatch.start("Load_Project")
    time.sleep(1.5)  # Simulate project load
    stopwatch.stop("Load_Project")
    
    stopwatch.start("Video_Export_4K")
    time.sleep(3.7)  # Simulate video export
    stopwatch.stop("Video_Export_4K")
    
    stopwatch.start("Save_Results")
    time.sleep(0.8)  # Simulate saving
    stopwatch.stop("Video_Export_4K")
    
    # Show visual summary
    stopwatch.print_summary()
    
    # Save to JSON
    stopwatch.save_json("demo_timings.json")
    print("\n✅ Timing data saved to demo_timings.json\n")

if __name__ == "__main__":
    demo_timing()
