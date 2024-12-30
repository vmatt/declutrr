import os
import shutil
import unittest
from unittest.mock import Mock, patch
from PIL import Image

from tests.generate_test_images import create_test_images
from declutrr.image_processor import ImageProcessor
from declutrr.constants import *

class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        from tests.fixtures import FIXTURES_DIR
        self.test_dir = os.path.join(FIXTURES_DIR, "test_photos")
        self.processor = ImageProcessor(self.test_dir)
        
        # Create test directories
        os.makedirs(self.test_dir, exist_ok=True)
        os.makedirs(self.processor.delete_dir, exist_ok=True)
        os.makedirs(self.processor.keep_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test environment after each test"""
        # Clean up the test_photos directory and its contents
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initialization of ImageProcessor"""
        self.assertEqual(self.processor.directory, self.test_dir)
        self.assertEqual(self.processor.delete_dir, os.path.join(self.test_dir, 'delete'))
        self.assertEqual(self.processor.keep_dir, os.path.join(self.test_dir, 'keep'))
        self.assertTrue(os.path.exists(self.processor.delete_dir))
        self.assertTrue(os.path.exists(self.processor.keep_dir))

    def test_load_image(self):
        """Test image loading"""
        from tests.fixtures import FIXTURES_DIR
        
        # Create and load actual test image
        create_test_images()
        test_image_path = os.path.join(FIXTURES_DIR, "test_photos", "image.jpg")
        
        result = ImageProcessor.load_image(test_image_path)
        
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (800, 600))  # Size from create_test_images

    def test_get_display_dimensions(self):
        """Test display dimension calculations"""
        # Test normal case
        width, height = ImageProcessor.get_display_dimensions(1000, 800)
        self.assertEqual(width, 1000 - WINDOW_PADDING)  # 1000 - WINDOW_PADDING
        self.assertEqual(height, 800 - CONTROLS_HEIGHT)  # 800 - CONTROLS_HEIGHT
        
        # Test minimum dimensions
        width, height = ImageProcessor.get_display_dimensions(0, 0)
        self.assertEqual(width, DEFAULT_WINDOW_WIDTH)  # DEFAULT_WINDOW_WIDTH
        self.assertEqual(height, DEFAULT_WINDOW_HEIGHT)  # DEFAULT_WINDOW_HEIGHT

    def test_move_file(self):
        """Test file moving functionality"""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test.jpg")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Test moving to delete directory
        self.processor.move_to_delete("test.jpg")
        self.assertTrue(os.path.exists(os.path.join(self.processor.delete_dir, "test.jpg")))
        self.assertFalse(os.path.exists(test_file))

        # Test restoring from delete directory
        self.processor.restore_from_delete("test.jpg")
        self.assertTrue(os.path.exists(test_file))
        self.assertFalse(os.path.exists(os.path.join(self.processor.delete_dir, "test.jpg")))

    def test_get_creation_time(self):
        """Test getting creation time from file system"""
        from tests.fixtures import FIXTURES_DIR
        
        # Create test images
        create_test_images()
        test_image_path = os.path.join(FIXTURES_DIR, "test_photos", "image.jpg")
        
        result = self.processor.get_creation_time(test_image_path)
        
        # Verify we get a valid timestamp
        self.assertIsInstance(result, float)
        self.assertTrue(result > 0)

    def test_get_image_files(self):
        """Test getting and sorting image files"""
        # Generate test images
        create_test_images()
        
        result = self.processor.get_image_files()
        
        # Should include all valid image filesn
        self.assertEqual(3, len(result))
        self.assertIn("image.jpg", result)
        self.assertIn("photo.jpeg", result)
        self.assertIn("graphic.png", result)

if __name__ == '__main__':
    unittest.main()
