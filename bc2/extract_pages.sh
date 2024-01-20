#!/bin/bash

# Function to standardize names
standardize_name() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^[:alnum:]]/_/g'
}

# Check if correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_folder> <destination_folder>"
    exit 1
fi

# Assign source and destination folders
src_folder="$1"
dst_folder="$2"

# Recursively find all PDF files in the source folder
find "$src_folder" -type f -name "*.pdf" | while read -r file; do

    echo $file
    
    # Get the relative path of the file, excluding the source folder path and the file extension
    relative_path="${file#$src_folder}"
    relative_path="${relative_path%.pdf}"

    # Standardize directory names
    standardized_dir=$(standardize_name "$relative_path")

    # Create a new directory in the destination folder with the same relative path
    new_dir="$dst_folder$standardized_dir"
    mkdir -p "$new_dir"

    # Standardize filenames
    standardized_filename=$(standardize_name "${relative_path##*/}")

    case_id=$(echo "$relative_path" | awk -F'/' '{print $1}')

    pdfseparate "$file" "$new_dir/${case_id}_${relative_path##*/}_page_%03d.pdf"

done
