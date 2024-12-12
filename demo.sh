#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -i INPUT_DIR -o OUTPUT_DIR -c CONFIG_FILE [-j NUM_JOBS]"
    echo "  -i INPUT_DIR    Specify the input directory."
    echo "  -o OUTPUT_DIR   Specify the output directory."
    echo "  -j NUM_JOBS     Specify the number of parallel jobs (default: 10)."
    echo "  -c CONFIG_FILE  Specify the TOML configuration file."
    exit 1
}

# Default number of jobs
NUM_JOBS=1

# Parse command-line arguments
while getopts "i:o:j:c:" opt; do
    case "$opt" in
        i) INPUT_DIR=$OPTARG ;;
        o) OUTPUT_DIR=$OPTARG ;;
        j) NUM_JOBS=$OPTARG ;;
        c) CONFIG_FILE=$OPTARG ;;
        *) usage ;;
    esac
done

# Check if input, output directories and config file are provided
if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ] || [ -z "$CONFIG_FILE" ]; then
    usage
fi

export OUTPUT_DIR
export CONFIG_FILE

# Create a temporary directory for modified TOML files
TEMP_DIR=$(mktemp -d)

# Clean up temporary directory on exit
trap 'rm -rf "$TEMP_DIR"' EXIT

export TEMP_DIR

process_file() {
    local file=$1
    filename=$(basename -- "$file")
    stripped_filename=${filename:4}  # Strip the last four characters
    temp_toml="$TEMP_DIR/${stripped_filename}.toml"
    sed "s/{{filename}}/${stripped_filename}/g" "$CONFIG_FILE" > "$temp_toml"
    poetry run python -m blind_charging_core "$temp_toml" --input-path "$file" --output-path "$OUTPUT_DIR/${filename}.pdf" --debug
}

export -f process_file

if [ "$NUM_JOBS" -eq 1 ]; then
    # Process files sequentially
    find "$INPUT_DIR" \( -name "*.txt" -o -name "*.pdf" \) | while read -r file; do
        process_file "$file"
    done
else
    # Process files in parallel
    find "$INPUT_DIR" \( -name "*.txt" -o -name "*.pdf" \) | parallel -j "$NUM_JOBS" --eta process_file {}
fi

osascript -e 'display notification "demo.sh finished" with title "Alert"' && afplay /System/Library/Sounds/Funk.aiff