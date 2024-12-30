#!/bin/bash

# Function to create folder and move file
move_file() {
	local file="$1"
	local folder="${file:4:6}"  # Extract YYYYMM from filename
	
	# Create folder if it doesn't exist
	mkdir -p "$folder"
	
	# Move file to the folder
	mv "$file" "$folder/"
	
	echo "Moved $file to $folder/"
}

# Main script
for file in IMG_*; do
	# Check if the file matches the pattern
	if [[ $file =~ ^IMG_[0-9]{8}_[0-9]{6}\.(JPG|PNG|MOV|MP4)$ ]]; then
		move_file "$file"
	else
		echo "Skipping $file: doesn't match the expected pattern"
	fi
done

echo "Organization complete!"
