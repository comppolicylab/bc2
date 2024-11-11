#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input_directory> <output_directory>"
    exit 1
fi

input_dir="$1"
output_dir="$2"
target_size=$((1000 * 1000 * 1000)) # 1GB in bytes
current_size=0

# Create the output directory if it doesn't exist
mkdir -p "$output_dir"

# Copy the fields.json file
if [ -f "$input_dir/fields.json" ]; then
    cp "$input_dir/fields.json" "$output_dir"
else
    echo "Warning: fields.json not found in the input directory."
fi

# Get a list of unique triplicate base names, ensuring we handle spaces
triplicates=$(find "$input_dir" -type f -name '*.pdf' | while read -r file; do echo "${file%.pdf}"; done | sort -u)

# Shuffle the list of triplicates
triplicates=$(echo "$triplicates" | shuf)

# Function to get the size of a file
get_size() {
    stat -f%z "$1"
}

# Process each triplicate
while IFS= read -r triplicate; do
    pdf_file="$triplicate.pdf"
    labels_file="$triplicate.pdf.labels.json"
    ocr_file="$triplicate.pdf.ocr.json"

    # Check if all files in the triplicate exist
    if [ -f "$pdf_file" ] && [ -f "$labels_file" ] && [ -f "$ocr_file" ]; then
        # Get the size of the triplicate files
        pdf_size=$(get_size "$pdf_file")
        labels_size=$(get_size "$labels_file")
        ocr_size=$(get_size "$ocr_file")
        triplicate_size=$((pdf_size + labels_size + ocr_size))

        # Check if adding this triplicate will exceed the target size
        if [ $(($current_size + $triplicate_size)) -gt $target_size ]; then
            break
        fi

        # Copy the triplicate files to the output directory
        cp "$pdf_file" "$output_dir"
        cp "$labels_file" "$output_dir"
        cp "$ocr_file" "$output_dir"

        # Update the current size
        current_size=$(($current_size + $triplicate_size))
    fi
done <<< "$triplicates"

echo "Copied files to $output_dir, total size: $current_size bytes"
