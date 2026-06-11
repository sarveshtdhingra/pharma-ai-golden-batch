#!/usr/bin/env python3
"""
Main entry point for Pharma Golden Batch AI Tool
Run this file to start the Streamlit dashboard
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit dashboard"""
    
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run Streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/dashboard.py"])

if __name__ == "__main__":
    main()
