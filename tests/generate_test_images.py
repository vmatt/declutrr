from PIL import Image
import os

def create_test_images():
    """Create test images for unit testing"""
    from tests.fixtures import FIXTURES_DIR
    test_photos_dir = os.path.join(FIXTURES_DIR, "test_photos")
    
    # Create test_photos directory if it doesn't exist
    os.makedirs(test_photos_dir, exist_ok=True)
    
    # Create exactly one of each supported image type
    test_images = [
        ("image.jpg", (800, 600), "red"),      # Standard JPEG
        ("photo.jpeg", (600, 800), "blue"),    # Alternate JPEG extension
        ("graphic.png", (700, 700), "green")   # PNG format
    ]
    
    for filename, size, color in test_images:
        img = Image.new('RGB', size, color)
        filepath = os.path.join(test_photos_dir, filename)
        img.save(filepath, quality=95)  # Set JPEG quality for better test images
        
    # Create an invalid.txt file for testing
    invalid_path = os.path.join(test_photos_dir, "invalid.txt")
    with open(invalid_path, 'w') as f:
        f.write("This is not an image file")

if __name__ == "__main__":
    create_test_images()
