# Image file extensions
VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')

# File prefixes
KEPT_PREFIX = 'G_'

# UI Constants
INITIAL_WINDOW_SIZE = "900x700"
WINDOW_PADDING = 40
CONTROLS_HEIGHT = 100
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 500

# Image statuses
STATUS_KEPT = 'kept'
STATUS_DELETED = 'deleted'
STATUS_SKIPPED = 'skipped'

# Action types
ACTION_DELETE = "delete"
ACTION_KEEP = "keep"

# Key bindings and labels
KEY_BINDINGS = {
    'arrows': {
        'delete': '<Left>',
        'keep': '<Right>',
        'skip': '<Down>',
        'labels': {
            'delete': '← Delete',
            'keep': 'Keep →',
            'skip': '↓ Skip'
        }
    },
    'letters': {
        'delete': 'j',
        'keep': 'l',
        'skip': 'k',
        'labels': {
            'delete': 'Delete (J)',
            'keep': 'Keep (L)',
            'skip': 'Skip (K)'
        }
    }
}

# UI Layout
PADDING = {'padx': 5, 'pady': 5}

# Dialog messages
STARTUP_TITLE = "Declutrr"
COMPLETION_TITLE = "Processing Complete"
COMPLETION_MESSAGE = "Would you like to process another folder?"
