import os
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from declutrr.utils import get_directory
from declutrr.image_processor import ImageProcessor
from declutrr.constants import *


class ImageSorter:
    """GUI application for sorting images into keep/delete categories."""
    def __init__(self, root: tk.Tk):
        """Initialize the Image Sorter application."""
        self.root = root
        self.root.title(STARTUP_TITLE)
        
        # Initialize all attributes
        self.directory = None
        self.processor = None
        self.delete_dir = None
        self.keep_dir = None
        
        # UI components
        self.main_frame = None
        self.image_frame = None
        self.canvas = None
        self.image_container = None
        self.image_label = None
        self.controls_frame = None
        self.status_var = None
        self.status_bar = None
        
        # State
        self.current_index = 0
        self.image_files = []
        self.image_status = {}
        self.history = []
        self.current_image = None
        self.stats = {STATUS_KEPT: 0, STATUS_DELETED: 0}
        
        self.setup_startup_dialog()

    def setup_startup_dialog(self):
        """Show initial dialog with options to open folder or quit."""
        dialog_frame = ttk.Frame(self.root, padding="20")
        dialog_frame.pack(expand=True, fill='both')
        
        ttk.Button(dialog_frame, text="Open Folder", 
                  command=self.start_processing).pack(pady=10)
        ttk.Button(dialog_frame, text="Quit", 
                  command=self.root.quit).pack(pady=10)

    def start_processing(self):
        """Initialize the image processing interface."""
        # Clear the startup dialog
        for widget in self.root.winfo_children():
            widget.destroy()

        # Get working directory
        self.directory = get_directory()
        if not self.directory:
            self.root.quit()
            return

        # Initialize image processor
        self.processor = ImageProcessor(self.directory)
        
        # Initialize directories
        self.delete_dir = os.path.join(self.directory, 'delete')
        self.keep_dir = os.path.join(self.directory, 'keep')
        os.makedirs(self.delete_dir, exist_ok=True)
        os.makedirs(self.keep_dir, exist_ok=True)

        # Initialize UI components
        self.main_frame = None
        self.image_frame = None
        self.canvas = None
        self.image_container = None
        self.image_label = None
        self.controls_frame = None
        self.status_var = None
        self.status_bar = None

        
        # Setup UI
        self.setup_ui()
        
        # Load images
        self.load_directory()
        
        # Bind keys and events
        self.bind_keys()
        self.root.bind('<Configure>', self.on_resize)
        
    def setup_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Image display
        self.image_frame = ttk.Frame(self.main_frame)
        self.image_frame.pack(expand=True, fill='both')
        
        # Create a canvas for proper centering
        self.canvas = tk.Canvas(self.image_frame, highlightthickness=0)
        self.canvas.pack(expand=True, fill='both')
        
        # Create centered container frame inside canvas
        self.image_container = ttk.Frame(self.canvas)
        self.canvas.create_window(0, 0, anchor='center', window=self.image_container, tags='container')
        
        self.image_label = ttk.Label(self.image_container)
        self.image_label.pack(padx=5, pady=5)
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', lambda e: self.center_image_container())
        
        # Controls frame
        self.controls_frame = ttk.Frame(self.main_frame)
        self.controls_frame.pack(fill='x', pady=10)
        
        # Left-side buttons
        ttk.Button(self.controls_frame, text="Quit", command=self.root.quit).pack(side='left', padx=5)
        ttk.Button(self.controls_frame, text="Choose Folder", command=self.reset_and_restart).pack(side='left', padx=5)
        ttk.Button(self.controls_frame, text="Undo (Z)", command=self.undo_last_action).pack(side='left', padx=5)
        
        # Right-side buttons
        ttk.Button(self.controls_frame, text="Keep →", command=self.keep_image).pack(side='right', padx=5)
        ttk.Button(self.controls_frame, text="↓ Skip", command=self.skip_image).pack(side='right', padx=5)
        ttk.Button(self.controls_frame, text="← Delete", command=self.delete_image).pack(side='right', padx=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_bar.pack(fill='x', pady=(10, 0))
        
    def bind_keys(self):
        self.root.bind('<Left>', lambda e: self.delete_image())
        self.root.bind('<Right>', lambda e: self.keep_image())
        self.root.bind('<Down>', lambda e: self.skip_image())
        self.root.bind('z', lambda e: self.undo_last_action())
        
    def load_directory(self):
        # Get list of images sorted by creation date
        self.image_files = self.processor.get_image_files()
        
        if not self.image_files:
            self.status_var.set("No images found in directory")
            return
            
        self.display_current_image()
        
    def display_current_image(self) -> None:
        """Display the current image and update status."""
        if self.current_index >= len(self.image_files):
            self.current_index = 0
            
        if self._all_images_processed():
            self._show_completion_status()
            return
            
        self._skip_processed_images()
        self._load_and_display_current_image()
        self._update_status_bar()

    def _all_images_processed(self) -> bool:
        """Check if all images have been processed."""
        return not any(
            self.image_status.get(img) not in [STATUS_DELETED, STATUS_KEPT]
            for img in self.image_files
        )

    def _show_completion_status(self) -> None:
        """Display completion dialog with options to process another folder or quit."""
        # Clear the main interface
        for widget in self.root.winfo_children():
            widget.destroy()

        dialog_frame = ttk.Frame(self.root, padding="20")
        dialog_frame.pack(expand=True, fill='both')

        stats_message = f"Processing complete!\nImages kept: {self.stats[STATUS_KEPT]}\nImages deleted: {self.stats[STATUS_DELETED]}"
        ttk.Label(dialog_frame, text=stats_message).pack(pady=20)
        
        ttk.Label(dialog_frame, text=COMPLETION_MESSAGE).pack(pady=10)
        
        ttk.Button(dialog_frame, text="Process Another Folder", 
                  command=self.reset_and_restart).pack(pady=10)
        ttk.Button(dialog_frame, text="Quit", 
                  command=self.root.quit).pack(pady=10)


    def reset_and_restart(self):
        """Reset the application state and start over with a new folder."""
        # Clear all state
        self.stats = {STATUS_KEPT: 0, STATUS_DELETED: 0}
        self.current_index = 0
        self.image_files = []
        self.image_status = {}
        self.history = []
        self.current_image = None
        
        # Clear the UI
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Start fresh
        self.setup_startup_dialog()

    def _skip_processed_images(self) -> None:
        """Skip over already processed images."""
        while (self.current_index < len(self.image_files) and 
               self.image_status.get(self.image_files[self.current_index]) in [STATUS_DELETED, STATUS_KEPT]):
            self.current_index = (self.current_index + 1) % len(self.image_files)

    def _load_and_display_current_image(self) -> None:
        """Load and display the current image."""
        filename = self.image_files[self.current_index]
        filepath = os.path.join(self.directory, filename)
        self.current_image = self.processor.load_image(filepath)
        self.resize_image()

    def _update_status_bar(self) -> None:
        """Update the status bar with current progress."""
        total_images = len(self.image_files)
        current_position = self.current_index + 1
        filename = self.image_files[self.current_index]
        self.status_var.set(f"Image {current_position} of {total_images}: {filename}")
        
    def resize_image(self):
        if not self.current_image:
            return
            
        # Get current window size
        window_width = self.root.winfo_width() - 40  # Account for padding
        window_height = self.root.winfo_height() - 100  # Account for controls and padding
        
        if window_width <= 1 or window_height <= 1:  # Window not properly initialized yet
            window_width = 800
            window_height = 500
            
        # Calculate resize dimensions maintaining aspect ratio
        display_size = (window_width, window_height)
        
        # Create a copy of the original image for resizing
        resized_image = self.current_image.copy()
        resized_image.thumbnail(display_size, Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(resized_image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo  # Keep a reference
        
    def center_image_container(self):
        # Update the size of the canvas window to encompass the inner frame
        self.canvas.update_idletasks()
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        # Center the container
        self.canvas.coords('container', canvas_width/2, canvas_height/2)
        
    def on_resize(self, event):
        # Only handle main window resize events
        if event.widget == self.root:
            self.resize_image()
            self.center_image_container()
        
    def delete_image(self):
        if not self.image_files or self.current_index >= len(self.image_files):
            return
            
        current_file = self.image_files[self.current_index]
        if self.image_status.get(current_file) in ['deleted', 'kept']:
            return
            
        self.processor.move_to_delete(current_file)
        self.history.append((current_file, "delete"))
        self.stats["deleted"] += 1
        self.image_status[current_file] = 'deleted'
        
        self.current_index += 1
        if self.current_index >= len(self.image_files):
            self.current_index = 0
            
        self.display_current_image()
            
    def keep_image(self):
        if not self.image_files or self.current_index >= len(self.image_files):
            return
            
        current_file = self.image_files[self.current_index]
        if self.image_status.get(current_file) in ['deleted', 'kept']:
            return
            
        self.processor.move_to_keep(current_file)
        self.history.append((current_file, "keep"))
        self.stats["kept"] += 1
        self.image_status[current_file] = 'kept'
        
        self.current_index += 1
        if self.current_index >= len(self.image_files):
            self.current_index = 0
            
        self.display_current_image()
        
    def skip_image(self):
        if not self.image_files or self.current_index >= len(self.image_files):
            return
            
        current_file = self.image_files[self.current_index]
        current_status = self.image_status.get(current_file)
        
        # Only mark as skipped if not already processed (kept or deleted)
        if current_status not in ['deleted', 'kept']:
            self.image_status[current_file] = 'skipped'
        else:
            # Remove from image_status if it was kept or deleted
            if current_file in self.image_status:
                del self.image_status[current_file]
        
        self.current_index += 1
        if self.current_index >= len(self.image_files):
            # If we've gone through all images, start over with skipped ones
            self.current_index = 0
            # Clear only 'skipped' status to allow re-processing
            self.image_status = {k: v for k, v in self.image_status.items() 
                               if v in ['deleted', 'kept']}
            
        self.display_current_image()
        
    def undo_last_action(self):
        if not self.history:
            return
            
        filename, action = self.history.pop()
        
        if action == "delete":
            # Move file back from delete folder
            self.processor.restore_from_delete(filename)
            self.stats["deleted"] -= 1
            
        elif action == "keep":
            # Move file back from keep folder
            self.processor.restore_from_keep(filename)
            self.stats["kept"] -= 1
            
        # Remove the status for this file, so it can be processed again
        if filename in self.image_status:
            del self.image_status[filename]
            
        # Find the index of the undone file
        try:
            self.current_index = self.image_files.index(filename)
        except ValueError:
            # If not found, keep current index
            pass
            
        self.display_current_image()


def main():
    root = tk.Tk()
    root.geometry(INITIAL_WINDOW_SIZE)
    app = ImageSorter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
