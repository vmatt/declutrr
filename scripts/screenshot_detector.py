
import sys
import cv2
import numpy as np
import os
import shutil
import logging
from ultralytics import YOLO
from src.utils import setup_logging, get_directory

# Initialize YOLO model globally
model = YOLO('yolov8n.pt')

def detect_with_yolo(image_path: str) -> bool:
    """Use YOLOv8 to detect if image contains screens/monitors."""
    try:
        # Run inference
        results = model(image_path)
        
        # YOLO class names that indicate screens/monitors
        screen_classes = ['tv', 'laptop', 'cell phone', 'monitor']
        
        # Check results for screen-related objects
        for result in results:
            # Get class names for detected objects
            class_names = [model.names[int(cls)] for cls in result.boxes.cls]
            
            # Check confidence scores
            confidences = result.boxes.conf
            
            # Look for screen objects with high confidence
            for cls_name, conf in zip(class_names, confidences):
                if cls_name in screen_classes and conf > 0.5:
                    logging.debug(f"YOLO detected {cls_name} with confidence {conf:.2f}")
                    return True
                    
        return False
        
    except Exception as e:
        logging.error(f"YOLO detection error: {str(e)}")
        return False

def is_screenshot(image_path: str) -> bool:
    """
    Detect if an image is likely a screenshot using YOLO and traditional CV methods.
    
    Parameters:
    -----------
    image_path : str
        Path to the image file
        
    Returns:
    --------
    bool
        True if the image is likely a screenshot, False otherwise
    """
    try:
        logging.info(f"#### Processing {image_path} ####")
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return False
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Check for uniform background regions (both light and dark)
        total_pixels = gray.shape[0] * gray.shape[1]
        
        # Check for light regions
        _, light_binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
        light_pixels = cv2.countNonZero(light_binary)
        light_ratio = light_pixels / total_pixels
        
        # Check for dark regions
        _, dark_binary = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
        dark_pixels = cv2.countNonZero(dark_binary)
        dark_ratio = dark_pixels / total_pixels
        
        # Combined uniform region ratio
        uniform_ratio = max(light_ratio, dark_ratio)
        
        # 2. Edge detection to find perfectly horizontal and vertical lines
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        # Get image dimensions for line length calculations
        height, width = gray.shape
        min_line_length = min(height, width) * 0.2  # At least 20% of image dimension
        
        # Count horizontal and vertical lines
        h_lines = 0
        v_lines = 0
        
        if lines is not None:
            for line in lines:
                rho, theta = line[0]
                # Convert theta to degrees for easier comparison
                angle_deg = theta * 180 / np.pi
                
                # Calculate line endpoints
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                
                # Calculate potential line length
                if abs(b) < 0.01:  # Horizontal line
                    line_length = width
                elif abs(a) < 0.01:  # Vertical line
                    line_length = height
                else:
                    continue  # Skip diagonal lines
                
                # Only count lines that are long enough
                if line_length >= min_line_length:
                    # Check for horizontal lines (180° ± 0.5°)
                    if abs(angle_deg - 180) <= 0.5 or abs(angle_deg - 0) <= 0.5:
                        h_lines += 1
                    # Check for vertical lines (90° ± 0.5°)
                    elif abs(angle_deg - 90) <= 0.5:
                        v_lines += 1
        
        # First try YOLO detection
        if detect_with_yolo(image_path):
            logging.info("Screenshot detected by YOLO")
            return True
            
        # Fall back to traditional CV method
        is_screenshot = False
        if h_lines >= 3 and v_lines >= 3:  # Require both horizontal AND vertical lines
            if uniform_ratio > 0.25:  # Significant uniform regions
                logging.info("Screenshot detected by traditional CV")
                is_screenshot = True
                    
        # Log detection metrics for debugging
        logging.debug(f"Light ratio: {light_ratio:.3f}, Dark ratio: {dark_ratio:.3f}")
        logging.debug(f"Uniform ratio: {uniform_ratio:.3f}")
        logging.debug(f"Horizontal lines: {h_lines}, Vertical lines: {v_lines}")
                    
        return is_screenshot
        
    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return False

def detect(directory: str) -> None:
    """
    Detect and move screenshot images to a separate folder.

    Apply kernel computing gradient of image to detect horizontal edges typical of screenshots.

    Parameters
    ----------
    directory: str
        Path to directory containing images to process
    nprocess: int, default = 40
        Number of the processors.
    threshold: int, default = 3
        Minimum number of horizontal lines to classify as screenshot.
    """
    # Get list of valid image files
    valid_extensions = ('.jpg', '.jpeg', '.png')
    image_files = [f for f in os.listdir(directory)
                   if f.lower().endswith(valid_extensions)]

    if not image_files:
        logging.warning("No valid image files found in the directory")
        return

    logging.info(f"Found {len(image_files)} images to process")

    # Create screenshots directory if it doesn't exist
    screenshots_dir = os.path.join(directory, 'screenshots')
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        logging.info(f"Created directory for screenshots: {screenshots_dir}")

    # Statistics
    stats = {'processed': 0, 'screenshots': 0, 'failed': 0}

    # Process each image
    for filename in image_files:
        file_path = os.path.join(directory, filename)
        try:
            if is_screenshot(file_path):
                # Move to screenshots folder
                dest_path = os.path.join(screenshots_dir, filename)
                shutil.move(file_path, dest_path)
                stats['screenshots'] += 1
                logging.info(f"Moved screenshot: {filename}")
            stats['processed'] += 1
            
        except Exception as e:
            stats['failed'] += 1
            logging.error(f"Error processing {filename}: {str(e)}")

    # Log final statistics
    logging.info("Processing Summary:")
    logging.info(f"Total files processed: {stats['processed']}")
    logging.info(f"Screenshots detected and moved: {stats['screenshots']}")
    logging.info(f"Failed to process: {stats['failed']}")

def main() -> None:
    setup_logging('screenshot_detector')
    logging.info("Starting screenshot detection...")

    try:
        directory = get_directory()
        if not directory:
            logging.error("No directory selected. Exiting.")
            return

        logging.info(f"Processing directory: {directory}")
        detect(directory)
        logging.info("Processing complete!")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
