#!/bin/bash

# Create screenshots directory if it doesn't exist
mkdir -p screenshots

# Process all files at once using exiftool
exiftool "-if" '$ImageWidth eq "1125"' "-directory=./screenshots" \
    -recurse \
    -ext jpg -ext jpeg -ext png \
    -preserve \
    .

echo "Done! All screenshots have been moved."

