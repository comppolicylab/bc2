#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -i INPUT_DIR -o OUTPUT_DIR -c CONFIG_FILE [-j NUM_JOBS]"
    echo "  -i INPUT_DIR    Specify the input directory containing PDF files."
    echo "  -o OUTPUT_DIR   Specify the output directory for redacted PDF files."
    echo "  -j NUM_JOBS     Specify the number of parallel jobs (default: 10)."
    echo "  -c CONFIG_FILE  Specify the TOML configuration file."
    exit 1
}

# Default number of jobs
NUM_JOBS=10

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

find "$INPUT_DIR" -name "*.pdf" | parallel -j "$NUM_JOBS" --eta '
    filename=$(basename -- {});
    stripped_filename=${filename:4}  # Strip the first four characters
    base_filename=${stripped_filename%.pdf}  # Remove the .pdf extension
    temp_toml="$TEMP_DIR/${base_filename}.toml";
    sed "s/{{filename}}/${base_filename}/g" "$CONFIG_FILE" > "$temp_toml";
    poetry run python -m lib.blind_charging_core "$temp_toml" --input-path {} --output-path "$OUTPUT_DIR/${filename%.pdf}-redacted.pdf"
'