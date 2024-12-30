import cv2
import os
import sys
import shutil
import logging
from tqdm import tqdm

from src.utils import setup_logging, get_directory

def is_blurry(image_path: str, threshold: float = 90) -> bool:
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            return False
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        if laplacian_var < threshold:
            print("\n")
            logging.info(f"Blurry image: {image_path} - Variance: {laplacian_var:.2f}")
            return True
        return False
    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return False

def process_directory() -> None:
    # Get directory from argument or user
    directory = get_directory()
    if not directory:
        logging.error("No directory selected. Exiting.")
        return

    logging.info(f"Processing directory: {directory}")

    # Create blurry directory if it doesn't exist
    blurry_dir = os.path.join(directory, 'blurry')
    if not os.path.exists(blurry_dir):
        os.makedirs(blurry_dir)
        logging.info(f"Created directory for blurry images: {blurry_dir}")

    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png')

    # Get list of valid image files
    image_files = [f for f in os.listdir(directory)
                   if f.lower().endswith(valid_extensions) and os.path.isfile(os.path.join(directory, f))]

    if not image_files:
        logging.warning("No valid image files found in the directory")
        return

    logging.info(f"Found {len(image_files)} images to process")

    # Statistics
    stats = {
        'processed': 0,
        'blurry': 0,
        'failed': 0
    }

    # Process each image file with progress bar
    with tqdm(image_files, desc="Processing", unit="file") as pbar:
        for filename in pbar:
            file_path = os.path.join(directory, filename)
            
            try:
                if is_blurry(file_path, pbar=pbar):
                    # Move to blurry folder
                    shutil.move(file_path, os.path.join(blurry_dir, filename))
                    stats['blurry'] += 1
                    logging.info(f"Moved blurry image: {filename}")
                
                stats['processed'] += 1
            except Exception as e:
                stats['failed'] += 1
                logging.error(f"Error processing {filename}: {str(e)}")

    # Log final statistics
    logging.info("Processing Summary:")
    logging.info(f"Total files processed: {stats['processed']}")
    logging.info(f"Blurry images moved: {stats['blurry']}")
    logging.info(f"Failed to process: {stats['failed']}")

def main() -> None:
    setup_logging('blur_detector')
    logging.info("Starting blur detection processing...")

    try:
        process_directory()
        logging.info("Processing complete!")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
