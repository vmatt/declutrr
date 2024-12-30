import os
import shutil
import unittest
from unittest.mock import patch, Mock
import tkinter as tk
from PIL import Image
from declutrr.constants import *
from declutrr.declutrr import ImageSorter
from declutrr.image_processor import ImageProcessor
from tests.generate_test_images import create_test_images

def get_display_or_skip():
    """Helper to skip tests if no display available"""
    try:
        tk.Tk()
        return True
    except tk.TclError:
        try:
            # Try using Xvfb if available
            import subprocess
            subprocess.run(['which', 'Xvfb'], check=True)
            return 'Xvfb'
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

class TestImageSorter(unittest.TestCase):
    @classmethod 
    def setUpClass(cls):
        """Set up test environment for all tests"""
        cls.display_type = get_display_or_skip()
        if cls.display_type == 'Xvfb':
            import subprocess
            # Start Xvfb
            cls.xvfb_process = subprocess.Popen(['Xvfb', ':99'])
            os.environ['DISPLAY'] = ':99'
        elif not cls.display_type:
            raise unittest.SkipTest("No display available and Xvfb not found")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests"""
        if hasattr(cls, 'xvfb_process'):
            cls.xvfb_process.terminate()
            cls.xvfb_process.wait()

    def setUp(self):
        """Set up test environment"""
        # Ensure we have test images
        create_test_images()
        
        self.root = tk.Tk()
        self.app = ImageSorter(self.root)

    def tearDown(self):
        """Clean up after tests"""
        # Clean up the test_photos directory
        from tests.fixtures import FIXTURES_DIR
        test_photos_dir = os.path.join(FIXTURES_DIR, "test_photos")
        if os.path.exists(test_photos_dir):
            shutil.rmtree(test_photos_dir)
        self.root.destroy()

    def test_init(self):
        """Test initialization of ImageSorter"""
        self.assertIsInstance(self.app.root, tk.Tk)
        self.assertEqual(self.app.root.title(), STARTUP_TITLE)

    @patch('declutrr.photo_swiper.get_directory')
    def test_start_processing_no_directory(self, mock_get_directory):
        """Test start_processing when no directory is selected"""
        mock_get_directory.return_value = None
        self.app.start_processing()
        # Should quit if no directory selected
        mock_get_directory.assert_called_once()

    def test_reset_and_restart(self):
        """Test reset and restart functionality"""
        # Set some initial state
        self.app.stats = {"kept": 5, "deleted": 3}
        self.app.current_index = 10
        self.app.image_files = ["test1.jpg", "test2.jpg"]
        
        # Reset
        self.app.reset_and_restart()
        
        # Verify state is reset
        self.assertEqual(self.app.stats, {"kept": 0, "deleted": 0})
        self.assertEqual(self.app.current_index, 0)
        self.assertEqual(self.app.image_files, [])
        self.assertEqual(self.app.image_status, {})
        self.assertEqual(self.app.history, [])
        self.assertIsNone(self.app.current_image)

    def test_all_images_processed(self):
        """Test _all_images_processed check"""
        self.app.image_files = ["test1.jpg", "test2.jpg"]
        self.app.image_status = {
            "test1.jpg": "kept",
            "test2.jpg": "deleted"
        }
        self.assertTrue(self.app._all_images_processed())
        
        # Test with unprocessed image
        self.app.image_status["test2.jpg"] = "skipped"
        self.assertFalse(self.app._all_images_processed())

    def test_skip_image(self):
        """Test skip image functionality"""
        from tests.fixtures import FIXTURES_DIR
        
        # Test with no images
        self.app.image_files = []
        self.app.skip_image()
        self.assertEqual(self.app.current_index, 0)
        
        # Setup test environment
        create_test_images()
        self.app.setup_ui()
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        self.app.image_files = ["image.jpg", "photo.jpeg", "graphic.png"]
        self.app.current_index = 0
        self.app.image_status = {}
        
        # Test normal skip
        with patch.object(self.app, '_load_and_display_current_image'), \
             patch.object(self.app, 'resize_image'):
            self.app.skip_image()
        self.assertEqual(self.app.current_index, 1)
        self.assertEqual(self.app.image_status["image.jpg"], "skipped")
        
        # Test skipping already processed image
        self.app.image_status["photo.jpeg"] = "kept"
        with patch.object(self.app, '_load_and_display_current_image'), \
             patch.object(self.app, 'resize_image'):
            self.app.skip_image()
        self.assertEqual(self.app.current_index, 2)
        self.assertNotIn("photo.jpeg", self.app.image_status)  # Shouldn't change kept status
        
        # Test wrap-around and status clearing
        with patch.object(self.app, '_load_and_display_current_image'), \
             patch.object(self.app, 'resize_image'):
            self.app.skip_image()  # Skip last image
        self.assertEqual(self.app.current_index, 0)  # Should wrap to start
        self.assertNotIn("image.jpg", self.app.image_status)  # Skipped status should be cleared

    def test_undo_last_action(self):
        """Test undo functionality for both delete and keep actions"""
        from tests.fixtures import FIXTURES_DIR
        
        # Setup test data and processor
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        
        # Test undo delete
        self.app.history = [("test1.jpg", "delete")]
        self.app.stats = {"deleted": 1, "kept": 0}
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('shutil.move') as mock_move:
                self.app.undo_last_action()
                
                # Verify the undo delete operation
                self.assertEqual(self.app.history, [])
                self.assertEqual(self.app.stats["deleted"], 0)
                mock_move.assert_called_once()

        # Test undo keep
        self.app.history = [("test2.jpg", "keep")]
        self.app.stats = {"deleted": 0, "kept": 1}
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('shutil.move') as mock_move:
                self.app.undo_last_action()
                
                # Verify the undo keep operation
                self.assertEqual(self.app.history, [])
                self.assertEqual(self.app.stats["kept"], 0)
                mock_move.assert_called_once()

    def test_load_directory(self):
        """Test loading directory with images"""
        from tests.fixtures import FIXTURES_DIR
        
        # Setup test environment
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        
        # Test with actual images
        self.app.setup_ui()  # Setup UI components needed for display
        create_test_images()
        
        # Set directory to test_photos
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        
        # Mock display methods to avoid tkinter image issues
        with patch.object(self.app, '_load_and_display_current_image'), \
             patch.object(self.app, 'resize_image'):
            self.app.load_directory()
        
        # Verify images were loaded
        self.assertEqual(len(self.app.image_files), 3)  # We create 3 test images
        self.assertIn("image.jpg", self.app.image_files)
        self.assertIn("photo.jpeg", self.app.image_files)
        self.assertIn("graphic.png", self.app.image_files)
        
        # Test with no images
        with patch.object(self.app.processor, 'get_image_files') as mock_get_files:
            mock_get_files.return_value = []
            self.app.load_directory()
            self.assertEqual(self.app.status_var.get(), "No images found in directory")

    def test_display_current_image(self):
        """Test display_current_image functionality"""
        from tests.fixtures import FIXTURES_DIR
        
        # Setup test environment
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        self.app.image_files = ["test1.jpg", "test2.jpg"]
        self.app.current_index = 0
        
        # Test when all images are processed
        self.app.image_status = {"test1.jpg": "kept", "test2.jpg": "kept"}
        with patch.object(self.app, '_show_completion_status') as mock_completion:
            self.app.display_current_image()
            mock_completion.assert_called_once()

        # Test skip processed images with real images
        create_test_images()
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        self.app.image_files = ["image.jpg", "photo.jpeg", "graphic.png"]
        self.app.image_status = {"image.jpg": "kept", "photo.jpeg": None}
        self.app.current_index = 0
        self.app.setup_ui()
        
        # Mock the display methods to avoid tkinter image issues
        with patch.object(self.app, '_load_and_display_current_image'), \
             patch.object(self.app, 'resize_image'):
            self.app.display_current_image()
        self.assertEqual(self.app.current_index, 1)
        self.assertEqual(self.app.status_var.get(), "Image 2 of 3: photo.jpeg")

    def test_resize_image(self):
        """Test image resizing functionality"""
        from tests.fixtures import FIXTURES_DIR
        
        # Setup UI components needed for resize
        self.app.setup_ui()
        
        # Test with no current image
        self.app.current_image = None
        self.app.resize_image()  # Should not raise exception
        
        # Create test images and load one
        create_test_images()
        test_image_path = os.path.join(FIXTURES_DIR, "test_photos", "image.jpg")
        self.app.current_image = Image.open(test_image_path)
        
        # Test resize with actual image
        original_size = self.app.current_image.size
        
        # Mock the image label configuration to avoid tkinter issues
        with patch.object(self.app.image_label, 'configure') as mock_configure:
            self.app.resize_image()
            mock_configure.assert_called_once()
        
        # Verify image was resized (PhotoImage created)
        self.assertIsNotNone(self.app.image_label.image)
        # Verify original image wasn't modified
        self.assertEqual(self.app.current_image.size, original_size)

    def test_center_image_container(self):
        """Test centering image container"""
        # Setup mock canvas without triggering setup_ui() to avoid double binding
        self.app.canvas = Mock()
        self.app.canvas.winfo_width.return_value = 800
        self.app.canvas.winfo_height.return_value = 600
        
        with patch.object(self.app.canvas, 'coords') as mock_coords:
            self.app.center_image_container()
            mock_coords.assert_called_once_with('container', 400, 300)

    def test_on_resize(self):
        """Test window resize handling"""
        # Mock event
        mock_event = Mock()
        mock_event.widget = self.app.root
        
        with patch.object(self.app, 'resize_image') as mock_resize:
            with patch.object(self.app, 'center_image_container') as mock_center:
                self.app.on_resize(mock_event)
                mock_resize.assert_called_once()
                mock_center.assert_called_once()

    def test_delete_and_keep_image(self):
        """Test delete and keep image functionality"""
        from tests.fixtures import FIXTURES_DIR
        
        # Setup test environment
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        
        # Setup with real images
        create_test_images()
        self.app.setup_ui()
        self.app.directory = os.path.join(FIXTURES_DIR, "test_photos")
        self.app.processor = ImageProcessor(self.app.directory)
        self.app.image_files = ["image.jpg", "photo.jpeg", "graphic.png"]
        self.app.current_index = 0
        self.app.stats = {"deleted": 0, "kept": 0}
        
        # Mock the display methods to avoid tkinter image issues
        with patch.object(self.app, 'display_current_image'), \
             patch.object(self.app, '_load_and_display_current_image'), \
             patch.object(self.app, 'resize_image'):
            
            # Test delete image
            self.app.delete_image()
            self.assertEqual(self.app.stats["deleted"], 1)
            self.assertEqual(self.app.image_status["image.jpg"], "deleted")
            self.assertEqual(self.app.current_index, 1)
            self.assertTrue(os.path.exists(os.path.join(self.app.directory, "delete", "image.jpg")))
            
            # Test keep image
            self.app.keep_image()
            self.assertEqual(self.app.stats["kept"], 1)
            self.assertEqual(self.app.image_status["photo.jpeg"], "kept")
            self.assertEqual(self.app.current_index, 2)
            self.assertTrue(os.path.exists(os.path.join(self.app.directory, "keep", "photo.jpeg")))

if __name__ == '__main__':
    unittest.main()
