#!/bin/bash

# Function to check if exiftool is installed
if ! command -v exiftool &> /dev/null; then
    echo "Error: exiftool is not installed"
    echo "Please install it using:"
    echo "  Ubuntu/Debian: sudo apt-get install libimage-exiftool-perl"
    echo "  MacOS: brew install exiftool"
    exit 1
fi

# Set color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Batch process all files
exiftool -if '$CreateDate || $DateTimeOriginal' \
    -fileOrder CreateDate \
    -d "IMG_%Y%m%d_%H%M%S-%%f.%%e" \
    '-filename<${CreateDate}' \
    '-filename<${DateTimeOriginal}' \
    -ext jpg -ext jpeg -ext png \
    -preserveDate \
    . \
    2>&1 | while read -r line; do
        if [[ $line == *"Error"* ]] || [[ $line == *"Warning"* ]]; then
            echo -e "${RED}${line}${NC}"
        else
            echo -e "${GREEN}${line}${NC}"
        fi
    done

# Now let's clean up the filenames to remove the original filename part
for file in IMG_*-*.jpg IMG_*-*.jpeg IMG_*-*.png; do
    if [[ -f "$file" ]]; then
        # Extract base parts
        base="${file%-*}"
        ext="${file##*.}"
        
        # Find next available number
        counter=1
        newname="${base}.${ext}"
        while [[ -f "$newname" ]]; do
            newname="${base}_${counter}.${ext}"
            ((counter++))
        done
        
        mv "$file" "$newname"
        echo -e "${GREEN}Cleaned up: $file -> $newname${NC}"
    fi
done

echo "Done!"

