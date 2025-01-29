import os
import logging
from typing import Tuple


def is_kept_file(filepath: str) -> bool:
    """Check if file is marked as kept by G_ prefix"""
    return os.path.basename(filepath).startswith('G_')


def mark_as_kept(filepath: str) -> bool:
    """Mark file as kept by adding G_ prefix"""
    try:
        directory = os.path.dirname(filepath)
        old_name = os.path.basename(filepath)
        if old_name.startswith('G_'):
            return True

        new_name = f"G_{old_name}"
        new_path = os.path.join(directory, new_name)
        
        # Use os.rename instead of shutil.move to keep it in same filesystem
        os.rename(filepath, new_path)

        return True
    except Exception as e:
        logging.warning(f"Error marking file as kept: {e}")
        return False

def unmark_as_kept(filepath: str) -> bool:
    """Remove G_ prefix from filename"""
    try:
        directory = os.path.dirname(filepath)
        old_name = os.path.basename(filepath)
        if not old_name.startswith('G_'):
            return True

            
        new_name = old_name[2:]  # Remove 'G_' prefix
        new_path = os.path.join(directory, new_name)
        
        # Use os.rename instead of shutil.move
        os.rename(filepath, new_path)

        return True
    except Exception as e:
        logging.warning(f"Error unmarking file: {e}")
        return False
