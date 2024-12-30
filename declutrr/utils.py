import os
import sys
import logging
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

def setup_logging(script_name: str) -> None:
    """
    Setup logging configuration with customizable script name
    
    Parameters:
    -----------
    script_name : str
        Name of the script for the log file
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Setup logging with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/{script_name}_{timestamp}.log'),
            logging.StreamHandler()
        ]
    )

def get_cli_path() -> str | None:
    """Get directory path from command line arguments if provided"""
    return sys.argv[1] if len(sys.argv) > 1 else None

def get_directory() -> str | None:
    """
    Get directory path from CLI argument or file dialog
    
    Returns:
    --------
    str or None
        Selected/provided directory path or None if cancelled/invalid
    """
    # First try command line argument
    cli_path = get_cli_path()
    if cli_path:
        if os.path.isdir(cli_path):
            return os.path.abspath(cli_path)
        else:
            logging.error(f"Invalid directory path: {cli_path}")
            return None
            
    # If no CLI path, use file dialog
    root = tk.Tk()
    root.withdraw()
    
    directory = filedialog.askdirectory(
        title='Select folder with images to process',
        initialdir='~'
    )
    
    return directory
