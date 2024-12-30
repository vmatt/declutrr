from ultralytics import YOLO
import os
import sys
import xattr
from tqdm import tqdm
import logging
from src.utils import setup_logging, get_directory


def add_finder_tags(file_path: str, tags: list[str]) -> bool:
    try:
        if not os.path.exists(file_path):
            logging.error(f"File '{file_path}' does not exist.")
            return False

        tag_key = 'com.apple.metadata:_kMDItemUserTags'
        tags_xml = '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><array>'

        for tag in tags:
            tags_xml += f'<string>{tag}</string>'

        tags_xml += '</array></plist>'

        xattr.setxattr(file_path, tag_key, tags_xml.encode('utf-8'))
        logging.info(f"Successfully added tags {tags} to '{file_path}'")
        return True

    except Exception as e:
        logging.error(f"Error adding tags to {file_path}: {str(e)}")
        return False



def process_images_in_directory() -> None:
    # Get directory from argument or user
    directory = get_directory()
    if not directory:
        logging.error("No directory selected. Exiting.")
        return

    logging.info(f"Processing directory: {directory}")

    # Initialize YOLOv8 classification and detection models
    logging.info("Loading YOLO models...")
    cls_model = YOLO('util/yolo11l-cls.pt')  # classification model
    det_model = YOLO('util/yolo11l.pt')      # detection model
    logging.info("Models loaded successfully")

    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png')

    # Get list of valid image files
    image_files = [f for f in os.listdir(directory)
                   if f.lower().endswith(valid_extensions)]

    if not image_files:
        logging.warning("No valid image files found in the current directory")
        return

    logging.info(f"Found {len(image_files)} images to process")

    # Statistics
    stats = {
        'processed': 0,
        'tagged': 0,
        'failed': 0,
        'no_classifications': 0
    }

    # Process each image file with progress bar
    for filename in tqdm(image_files, desc="Processing images", unit="file"):
        file_path = os.path.join(directory, filename)
        logging.info(f"\nProcessing {filename}")

        try:
            # Perform classification and detection
            cls_results = cls_model(file_path)
            det_results = det_model(file_path)
            stats['processed'] += 1

            # Extract classifications above confidence threshold
            classifications = []
            
            # Process classification results - get top 2
            for result in cls_results:
                probs = result.probs
                # Convert to list of (class_name, confidence) tuples and sort
                cls_pairs = [(result.names[i], conf.item()) for i, conf in enumerate(probs.data)]
                cls_pairs.sort(key=lambda x: x[1], reverse=True)
                # Take top 2 classifications
                classifications.extend(cls_pairs[:2])

            # Process detection results - get top 4
            for result in det_results:
                # Convert to list of (class_name, confidence) tuples and sort
                det_pairs = [(result.names[int(box.cls)], box.conf.item()) for box in result.boxes]
                det_pairs.sort(key=lambda x: x[1], reverse=True)
                # Take top 4 detections
                classifications.extend(det_pairs[:4])

            if classifications:
                # Sort by confidence (highest first)
                classifications.sort(key=lambda x: x[1], reverse=True)
                # Remove duplicates while preserving order
                seen = set()
                unique_classifications = []
                for class_name, conf in classifications:
                    if class_name not in seen:
                        seen.add(class_name)
                        unique_classifications.append((class_name, conf))
                # Limit to top 10 unique tags
                unique_classifications = unique_classifications[:10]
                tags = [class_name for class_name, _ in unique_classifications]

                logging.info(f"Classifications for {filename}:")
                for class_name, conf in classifications:
                    logging.info(f"- {class_name}: {conf:.2f}")

                # Add tags to the file
                if add_finder_tags(file_path, tags):
                    stats['tagged'] += 1
                else:
                    stats['failed'] += 1
            else:
                logging.info(f"No classifications above threshold for {filename}")
                stats['no_classifications'] += 1

        except Exception as e:
            stats['failed'] += 1
            logging.error(f"Error processing {filename}: {str(e)}")

    # Log final statistics
    logging.info("Processing Summary:")
    logging.info(f"Total files processed: {stats['processed']}")
    logging.info(f"Successfully tagged: {stats['tagged']}")
    logging.info(f"Files with no classifications above threshold: {stats['no_classifications']}")
    logging.info(f"Failed to process: {stats['failed']}")


def main() -> None:
    setup_logging('auto_tagger')
    logging.info("Starting image processing and tagging...")

    try:
        process_images_in_directory()
        logging.info("Processing complete!")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
