from typing import Tuple, Union
from os import PathLike
import os
import shutil
import logging

from PIL import Image
from declutrr.constants import *

PathType = Union[str, PathLike[str]]


class ImageProcessor:
    def __init__(self, base_directory: str):
        self.directory = base_directory
        self.delete_dir = os.path.join(base_directory, 'delete')
        self.keep_dir = os.path.join(base_directory, 'keep')
        os.makedirs(self.delete_dir, exist_ok=True)
        os.makedirs(self.keep_dir, exist_ok=True)

    @staticmethod
    def load_image(filepath: str) -> Image.Image:
        """Load an image from the given filepath."""
        return Image.open(filepath)

    @staticmethod
    def get_display_dimensions(window_width: int, window_height: int) -> Tuple[int, int]:
        """Calculate proper display dimensions accounting for UI elements."""
        if window_width <= 1 or window_height <= 1:
            return DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
        
        return (
            window_width - WINDOW_PADDING,
            window_height - CONTROLS_HEIGHT
        )

    @staticmethod
    def move_file(filename: PathType, source_dir: PathType, dest_dir: PathType) -> None:
        """Move a file between directories."""
        source = os.path.join(source_dir, filename)
        destination = os.path.join(dest_dir, filename)
        shutil.move(source, destination)

    def move_to_delete(self, filename: str) -> None:
        """Move file to delete directory."""
        self.move_file(filename, self.directory, self.delete_dir)

    def restore_from_delete(self, filename: str) -> None:
        """Restore file from delete directory."""
        self.move_file(filename, self.delete_dir, self.directory)

    def restore_from_keep(self, filename: str) -> None:
        """Restore file from keep directory."""
        self.move_file(filename, self.keep_dir, self.directory)

    def move_to_keep(self, filename: str) -> None:
        """Move file to keep directory."""
        self.move_file(filename, self.directory, self.keep_dir)

    @staticmethod
    def get_creation_time(filepath: str) -> float:
        """Get creation time from EXIF data or file system."""
        try:
            with Image.open(filepath) as img:
                exif = img._getexif()
                if exif is not None:
                    # Try different EXIF tags for creation date
                    for tag in [36867, 36868, 306]:  # DateTimeOriginal, DateTimeDigitized, DateTime
                        if tag in exif:
                            try:
                                # Convert EXIF date string to timestamp
                                date_str = exif[tag]
                                # EXIF date format: 'YYYY:MM:DD HH:MM:SS'
                                from datetime import datetime
                                dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                                return dt.timestamp()
                            except (ValueError, TypeError):
                                continue
        except Exception as e:
            logging.error(f"Error reading EXIF data: {e}")
            pass
        
        # Fallback to filesystem creation time
        return os.path.getctime(filepath)

    def get_image_files(self) -> list[str]:
        """Get list of valid image files in directory, sorted by creation date."""
        files = [
            f for f in os.listdir(self.directory)
            if f.lower().endswith(VALID_IMAGE_EXTENSIONS) and 
            os.path.isfile(os.path.join(self.directory, f))
        ]
        
        # Sort files by creation time (EXIF or filesystem)
        return sorted(
            files,
            key=lambda x: self.get_creation_time(os.path.join(self.directory, x))
        )
