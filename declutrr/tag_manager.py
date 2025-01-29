from typing import List
from xattr import xattr

# Finder color tag mapping
FINDER_COLORS = {
    0: 'none',
    1: 'gray',
    2: 'green',
    3: 'purple', 
    4: 'blue',
    5: 'yellow',
    6: 'red',
    7: 'orange'
}

def get_file_tags(filepath: str) -> List[str]:
    """Get Finder color tag for a file"""
    try:
        attrs = xattr(filepath)
        finder_attrs = attrs.get('com.apple.FinderInfo')
        if finder_attrs is not None:
            color_num = finder_attrs[9] >> 1 & 7
            color = FINDER_COLORS.get(color_num, 'none')
            return [color] if color != 'none' else []
    except OSError:
        return []
    except Exception as e:
        print(f"Error getting tag: {e}")
    return []

def add_green_tag(filepath: str) -> bool:
    """Add green tag to file using Finder color tags"""
    try:
        attrs = xattr(filepath)
        # Create new FinderInfo if it doesn't exist
        finder_attrs = bytearray(b'\x00' * 32)
        # Set color to green (2)
        finder_attrs[9] = 2 << 1
        # Write the attributes
        attrs['com.apple.FinderInfo'] = bytes(finder_attrs)
        return True
    except Exception as e:
        print(f"Error adding tag: {e}")
        return False
