from typing import Tuple, Union, List
from os import PathLike
import os
import logging
import shutil

from PIL import Image
from declutrr.constants import *
from declutrr.file_manager import is_kept_file, mark_as_kept

PathType = Union[str, PathLike[str]]


class ImageProcessor:
    def __init__(self, base_directory: str):
        self.directory = base_directory
        self.delete_dir = os.path.join(base_directory, 'delete')
        os.makedirs(self.delete_dir, exist_ok=True)

    @staticmethod
    def load_image(filepath: str) -> Image.Image | None:
        """
        Load an image from the given filepath and apply EXIF rotation if needed.
        Returns None if file doesn't exist or can't be opened.
        """
        if not os.path.exists(filepath):
            return None
            
        image = None
        try:
            image = Image.open(filepath)
            # Get EXIF data
            exif = image._getexif()
            if exif is not None:
                # EXIF orientation tag
                orientation = exif.get(274)  # 274 is the orientation tag
                if orientation is not None:
                    # Create new image with correct dimensions for 90/270 degree rotations
                    if orientation in [5, 6, 7, 8]:
                        # For 90° or 270° rotations, swap width and height
                        new_width = image.height
                        new_height = image.width
                        rotated_image = Image.new(image.mode, (new_width, new_height))
                    else:
                        rotated_image = Image.new(image.mode, image.size)

                    # Rotate and/or flip based on EXIF orientation
                    if orientation == 2:
                        image = image.transpose(Image.FLIP_LEFT_RIGHT)
                    elif orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 4:
                        image = image.transpose(Image.FLIP_TOP_BOTTOM)
                    elif orientation == 5:
                        image = image.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                    elif orientation == 6:
                        image = image.rotate(-90, expand=True)
                    elif orientation == 7:
                        image = image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)

        except Exception as e:
            logging.warning(f"Error processing EXIF rotation for {filepath}: {e}")
            
        return image

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
        
        # Ensure destination doesn't exist
        if os.path.exists(destination):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(destination):
                new_name = f"{base}_{counter}{ext}"
                destination = os.path.join(dest_dir, new_name)
                counter += 1
                
        shutil.move(source, destination)

    def move_to_delete(self, filename: str) -> None:
        """Move file to delete directory."""
        self.move_file(filename, self.directory, self.delete_dir)

    def restore_from_delete(self, filename: str) -> None:
        """Restore file from delete directory."""
        self.move_file(filename, self.delete_dir, self.directory)


    def mark_as_kept(self, filepath: str) -> bool:
        """Mark file as kept by adding G_ prefix."""
        return mark_as_kept(filepath)

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
        files = []
        for f in os.listdir(self.directory):
            if not f.lower().endswith(VALID_IMAGE_EXTENSIONS):
                continue
                
            filepath = os.path.join(self.directory, f)
            if not os.path.isfile(filepath):
                continue
                
            # Skip files that are marked as kept with G_ prefix
            if is_kept_file(filepath):
                continue
                
            files.append(f)
        
        # Sort files by creation time (EXIF or filesystem)
        return sorted(
            files,
            key=lambda x: self.get_creation_time(os.path.join(self.directory, x))
        )
